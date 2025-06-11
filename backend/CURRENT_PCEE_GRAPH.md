---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	Task_Setup(Task_Setup)
	Librarian(Librarian)
	Chief_Architect(Chief_Architect)
	Site_Foreman(Site_Foreman)
	Worker(Worker)
	Project_Supervisor(Project_Supervisor)
	Advance_To_Next_Step(Advance_To_Next_Step)
	__end__([<p>__end__</p>]):::last
	Advance_To_Next_Step --> Site_Foreman;
	Chief_Architect --> Site_Foreman;
	Project_Supervisor -.-> Advance_To_Next_Step;
	Project_Supervisor -.-> __end__;
	Site_Foreman --> Worker;
	Task_Setup -.-> Chief_Architect;
	Task_Setup -.-> Librarian;
	Worker --> Project_Supervisor;
	__start__ --> Task_Setup;
	Librarian --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```