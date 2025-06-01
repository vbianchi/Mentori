# backend/tools/python_package_installer_tool.py
import logging
import asyncio
import sys
import re
from typing import Optional, Type, Any # Added Any

from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun
# <<< MODIFIED IMPORT: Using Pydantic v2 directly --- >>>
from pydantic import BaseModel, Field
# <<< --- END MODIFIED IMPORT --- >>>

from backend.config import settings

logger = logging.getLogger(__name__)

PACKAGE_SPEC_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+(?:\[[a-zA-Z0-9_,-]+\])?(?:[=<>!~]=?\s*[a-zA-Z0-9_.*-]+)?$")

class PythonPackageInstallerInput(BaseModel): # <<< Now inherits from Pydantic v2 BaseModel
    package_specifiers: str = Field(description="A string of one or more package specifiers, separated by spaces or commas (e.g., 'numpy pandas', 'matplotlib==3.5.0').")
    # No model_config needed for this simple model

class PythonPackageInstallerTool(BaseTool):
    name: str = "python_package_installer"
    description: str = (
        f"Use this tool ONLY to install Python packages into the current environment using 'uv pip install' or 'pip install'. "
        f"Input MUST be a string of one or more package specifiers, separated by spaces or commas "
        f"(e.g., 'numpy pandas', 'matplotlib==3.5.0', 'scikit-learn>=1.0 bokeh'). "
        f"**SECURITY WARNING:** This installs packages into the main environment. Avoid installing untrusted packages. "
        f"Timeout: {settings.tool_installer_timeout}s. "
        f"Returns a summary of the installation process, indicating success or failure for each package."
    )
    args_schema: Type[BaseModel] = PythonPackageInstallerInput

    async def _arun(
        self,
        package_specifiers_str: str, # Accepts the string directly
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any # <<< Any is now defined
    ) -> str:
        tool_name = self.name
        logger.info(f"Tool '{tool_name}' received raw input: '{package_specifiers_str}'")
        if not isinstance(package_specifiers_str, str) or not package_specifiers_str.strip():
            logger.error(f"Tool '{tool_name}': Received invalid input. Expected a non-empty string of package specifiers.")
            raise ToolException("Invalid input. Expected a non-empty string of package specifiers (space or comma separated).")

        timeout = settings.tool_installer_timeout
        individual_specs = [spec.strip() for spec in re.split(r'[\s,]+', package_specifiers_str) if spec.strip()]

        if not individual_specs:
            logger.error(f"Tool '{tool_name}': No valid package specifiers found after splitting input: '{package_specifiers_str}'.")
            raise ToolException("No package specifiers provided after cleaning the input string.")

        results_summary = []
        all_successful = True

        python_executable = sys.executable
        installer_command_base_parts = [python_executable, "-m"]
        try:
            # Check for 'uv'
            uv_check_process = await asyncio.create_subprocess_exec(
                python_executable, "-m", "uv", "--version",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await uv_check_process.wait()
            if uv_check_process.returncode == 0:
                logger.info(f"Tool '{tool_name}': Detected uv, using 'uv pip install'.")
                installer_command_base_parts.extend(["uv", "pip"])
            else:
                logger.info(f"Tool '{tool_name}': uv check failed or not found, falling back to 'pip install'.")
                installer_command_base_parts.append("pip")
        except Exception as uv_err:
            logger.warning(f"Tool '{tool_name}': Error checking for uv, falling back to pip: {uv_err}")
            installer_command_base_parts.append("pip")

        for single_spec in individual_specs:
            cleaned_package_specifier = single_spec.strip().strip('\'"`')
            if not cleaned_package_specifier:
                results_summary.append(f"Skipped empty specifier derived from input '{single_spec}'.")
                continue

            if not PACKAGE_SPEC_REGEX.match(cleaned_package_specifier):
                logger.error(f"Tool '{tool_name}': Invalid package specifier format rejected: '{cleaned_package_specifier}'.")
                results_summary.append(f"Error: Invalid package specifier format for '{cleaned_package_specifier}'. Installation skipped.")
                all_successful = False
                continue

            if ';' in cleaned_package_specifier or '&' in cleaned_package_specifier or '|' in cleaned_package_specifier or '`' in cleaned_package_specifier or '$(' in cleaned_package_specifier:
                logger.error(f"Tool '{tool_name}': Potential command injection detected in package specifier: '{cleaned_package_specifier}'.")
                results_summary.append(f"Error: Invalid characters detected in package specifier '{cleaned_package_specifier}'. Installation skipped.")
                all_successful = False
                continue

            logger.info(f"Tool '{tool_name}': Requesting install for package: '{cleaned_package_specifier}' (Timeout: {timeout}s)")

            command_to_run = installer_command_base_parts + ["install", cleaned_package_specifier]
            logger.info(f"Tool '{tool_name}': Executing installation command: {' '.join(command_to_run)}")

            process = None
            try:
                process = await asyncio.create_subprocess_exec(
                    *command_to_run,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                TIMEOUT_SECONDS = timeout
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
                except asyncio.TimeoutError:
                    logger.error(f"Tool '{tool_name}': Timeout installing package: {cleaned_package_specifier}")
                    if process and process.returncode is None:
                        try: process.terminate()
                        except ProcessLookupError: pass
                        await process.wait()
                    results_summary.append(f"Error installing '{cleaned_package_specifier}': Package installation timed out after {TIMEOUT_SECONDS} seconds.")
                    all_successful = False
                    continue

                stdout_str = stdout.decode(errors='replace').strip()
                stderr_str = stderr.decode(errors='replace').strip()
                return_code = process.returncode

                log_output_details = ""
                if stdout_str: log_output_details += f"--- STDOUT for {cleaned_package_specifier} ---\n{stdout_str}\n"
                if stderr_str: log_output_details += f"--- STDERR for {cleaned_package_specifier} ---\n{stderr_str}\n"

                if return_code == 0:
                    logger.info(f"Tool '{tool_name}': Successfully installed package: {cleaned_package_specifier}")
                    success_msg = f"Successfully installed '{cleaned_package_specifier}'."
                    if stderr_str:
                        success_msg += f" Notes/Warnings: {stderr_str[:200]}{'...' if len(stderr_str)>200 else ''}"
                    results_summary.append(success_msg)
                    if log_output_details: logger.debug(f"Tool '{tool_name}': Full log for '{cleaned_package_specifier}':\n{log_output_details}")
                else:
                    logger.error(f"Tool '{tool_name}': Failed to install package: {cleaned_package_specifier}. Exit code: {return_code}. Stderr: {stderr_str}")
                    error_details_for_summary = stderr_str if stderr_str else stdout_str
                    results_summary.append(f"Error installing '{cleaned_package_specifier}': Failed (Code: {return_code}). Details: {error_details_for_summary[:300]}{'...' if len(error_details_for_summary)>300 else ''}")
                    all_successful = False
                    if log_output_details: logger.debug(f"Tool '{tool_name}': Full log for failed '{cleaned_package_specifier}':\n{log_output_details}")

            except FileNotFoundError:
                logger.error(f"Tool '{tool_name}': Error installing package: '{installer_command_base_parts[0]}' command not found.")
                results_summary.append(f"Error installing '{cleaned_package_specifier}': Installer command ('{installer_command_base_parts[0]}') not found.")
                all_successful = False
            except Exception as e:
                logger.error(f"Tool '{tool_name}': Error installing package '{cleaned_package_specifier}': {e}", exc_info=True)
                results_summary.append(f"Error installing '{cleaned_package_specifier}': {type(e).__name__}.")
                all_successful = False
            finally:
                if process and process.returncode is None:
                    logger.warning(f"Tool '{tool_name}': Installer process '{' '.join(command_to_run)}' still running in finally block, attempting termination.")
                    try: process.terminate(); await process.wait()
                    except ProcessLookupError: pass
                    except Exception as term_e: logger.error(f"Tool '{tool_name}': Error during final termination attempt of installer: {term_e}")

        final_message = "Package installation process finished.\n" + "\n".join(results_summary)
        if not all_successful:
            return f"One or more packages failed to install. Full log:\n{final_message}"
        return final_message

    def _run(self, package_specifiers_str: str, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs: Any) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self._arun(package_specifiers_str=package_specifiers_str, run_manager=run_manager, **kwargs), loop)
                return future.result(timeout=settings.tool_installer_timeout + 10) # Add buffer
            else:
                return asyncio.run(self._arun(package_specifiers_str=package_specifiers_str, run_manager=run_manager, **kwargs))
        except Exception as e:
            logger.error(f"Error running PythonPackageInstallerTool synchronously for '{package_specifiers_str}': {e}", exc_info=True)
            return f"Error: {e}"
