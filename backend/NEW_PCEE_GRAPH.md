graph TD;
    __start__([_start_]):::first
    Task_Setup(Task_Setup)
    Librarian(Librarian)
    Chief_Architect(Chief_Architect)
    WaitFor_Plan_Approval(WaitFor_Plan_Approval):::hitl
    Site_Foreman(Site_Foreman)
    Worker(Worker)
    Project_Supervisor(Project_Supervisor)
    Advance_To_Next_Step(Advance_To_Next_Step)
    Correction_Planner(Correction_Planner):::correction
    WaitFor_Correction_Approval(WaitFor_Correction_Approval):::hitl
    __end__([__end__]):::last

    __start__ --> Task_Setup;

    subgraph Initial Routing
        Task_Setup -- "Router: Simple QA" --> Librarian;
        Task_Setup -- "Router: Complex Task" --> Chief_Architect;
    end
    
    Librarian --> __end__;

    subgraph Planning and Approval
        Chief_Architect --> WaitFor_Plan_Approval;
        WaitFor_Plan_Approval -- "Approve" --> Site_Foreman;
        WaitFor_Plan_Approval -- "Reject" --> __end__;
    end

    subgraph Execution Loop
        Site_Foreman --> Worker;
        Worker --> Project_Supervisor;
        Project_Supervisor -- "Success" --> Advance_To_Next_Step;
        Advance_To_Next_Step --> Site_Foreman;
        Project_Supervisor -- "Plan Complete" --> __end__;
    end

    subgraph Self-Correction Loop
        Project_Supervisor -- "Failure" --> Correction_Planner;
        Correction_Planner --> WaitFor_Correction_Approval;
        WaitFor_Correction_Approval -- "Approve" --> Site_Foreman;
        WaitFor_Correction_Approval -- "Reject" --> __end__;
    end
    
    classDef default fill:#f2f0ff,stroke:#888,line-height:1.2
    classDef first fill-opacity:0,stroke:none
    classDef last fill:#bfb6fc,stroke:#888
    classDef correction fill:#ffe0e0,stroke:#c00
    classDef hitl fill:#e0f2fe,stroke:#0369a1,stroke-width:2px