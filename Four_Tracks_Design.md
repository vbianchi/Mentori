graph TD
    subgraph Core Logic
        direction TB
        
        A[Task_Setup]:::nodeStyle
        B[Memory_Updater]:::nodeStyle
        C{History Management}:::conditionalStyle
        D[summarize_history_node]:::nodeStyle
        E{Initial Four-Track Router}:::conditionalStyle

        A --> B
        B --> C
        C -- Needs Summary --> D
        C -- No Summary Needed --> E
        D --> E

        subgraph Track 1: Direct QA
            direction LR
            F[Editor]:::nodeStyle
        end

        subgraph "Track 2: Simple Tool (Handyman)"
            direction TB
            G[Handyman]:::nodeStyle
            H_Worker["Worker"]:::nodeStyle
            G --> H_Worker
            H_Worker --> F
        end

        subgraph "Track 3: Standard Complex Project"
            direction TB
            I[Chief_Architect]:::nodeStyle
            J[Plan_Expander]:::nodeStyle
            K[/Approve Plan /]:::hitlStyle
            L{User Approved?}:::conditionalStyle
            
            I --> J --> K --> L
            L -- No --> F
        end
        
        subgraph "Track 4: Peer Review Session"
            direction TB
            T[Propose_Experts]:::nodeStyle
            U[/Approve Board /]:::hitlStyle
            V{Board Approved?}:::conditionalStyle
            
            T --> U --> V
            
            subgraph "Autonomous Plan Refinement Loop"
                W[Chair_Initial_Plan]:::nodeStyle
                X[Expert_Critique]:::nodeStyle
                Y[Chair_Final_Review]:::nodeStyle
                
                W --> X
                X -- each expert --> W
                W -- all critiques done --> Y
            end

            V -- Yes --> W
            V -- No --> F

            Y --> K
        end

        subgraph "Shared Execution & Review Engine"
            direction TB
            M[Site_Foreman]:::nodeStyle
            N[Worker]:::nodeStyle
            O[Project_Supervisor]:::nodeStyle
            P{Step Outcome}:::conditionalStyle
            
            M --> N --> O --> P

            subgraph "Self-Correction Sub-Loop"
                Q[Correction_Planner]:::correctionStyle
                Q -- Inserts new step --> M
            end

            subgraph "Autonomous Checkpoint Review"
               S_Editor["Editor (Compiles Report)"]:::nodeStyle
               S[Board_Collective_Review]:::nodeStyle
               S_Router{Board Decision}:::conditionalStyle
               S_HITL[/Provide Guidance /]:::hitlStyle

               S_Editor --> S
               S --> S_Router
               S_Router -- Continue --> M
               S_Router -- Adapt --> W
               S_Router -- Stuck --> S_HITL
               S_HITL --> W
            end

            P -- Success & More Steps --> M
            P -- Checkpoint Reached --> S_Editor
            P -- Failure & Retries Left --> Q
            P -- Plan Complete or Max Retries --> F
        end

        L -- Yes --> M

        E -- DIRECT_QA --> F
        E -- SIMPLE_TOOL_USE --> G
        E -- COMPLEX_PROJECT --> I
        E -- PEER_REVIEW --> T
        
        F --> Z([END]):::endStyle
    end

classDef nodeStyle fill:#1E2233,stroke:#676F8D,stroke-width:2px,color:#FFFFFF
classDef conditionalStyle fill:#5C6784,stroke:#A0A8C0,stroke-width:2px,color:#FFFFFF
classDef userInputStyle fill:#3B82F6,stroke:#93C5FD,stroke-width:2px,color:#FFFFFF
classDef endStyle fill:#E11D48,stroke:#F472B6,stroke-width:2px,color:#FFFFFF
classDef hitlStyle fill:#a43bfa,stroke:#d8b4fe,stroke-width:2px,color:#FFFFFF
classDef correctionStyle fill:#f97316,stroke:#fdba74,stroke-width:2px,color:#FFFFFF