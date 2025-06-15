graph TD
    %% --- Style Definitions ---
    classDef default fill:#27272a,stroke:#52525b,stroke-width:2px,color:#e4e4e7
    classDef startend fill:#4f46e5,stroke:#a5b4fc,stroke-width:2px,color:#ffffff
    classDef hitl fill:#0e7490,stroke:#67e8f9,stroke-width:2px,color:#f0f9ff
    classDef newnode fill:#166534,stroke:#4ade80,stroke-width:2px,color:#f0fdf4
    classDef router fill:#b45309,stroke:#fbbf24,stroke-width:2px,color:#fefce8

    %% --- Node Definitions ---
    subgraph Legend
        direction LR
        style Legend fill:none,stroke:none
        NewNode("New/Refactored Node"):::newnode
        RouterNode("Primary Router"):::router
        HITLNode("Human-in-the-Loop"):::hitl
        ExistingNode("Existing Logic"):::default
    end

    _start_([Start]):::startend
    Router("1.Router"):::router
    Editor("Unified Editor"):::newnode
    _end_([End]):::startend

    subgraph "Track 2: Simple Tool Use"
        Handyman("2b. Handyman"):::newnode
        Worker_Simple("3b. Worker"):::default
    end

    subgraph "Track 3: Complex Project"
        Chief_Architect("2c. Chief Architect"):::default
        WaitFor_Plan_Approval("3c. Wait For Plan Approval"):::hitl
        Site_Foreman("4c. Site Foreman"):::default
        Worker_Complex("5c. Worker"):::default
        Project_Supervisor("6c. Project Supervisor"):::default
        After_Step_Router{"7c. Outcome?"}:::default
    end

    %% --- Edge Connections ---
    _start_ -- "User Request" --> Router

    %% Track 1: Direct Q&A
    Router -- "Route: DIRECT_QA" --> Editor
    
    %% Track 2: Simple Tool Use
    Router -- "Route: SIMPLE_TOOL_USE" --> Handyman
    Handyman -- "Formulate Single Action" --> Worker_Simple
    Worker_Simple -- "Execute Action" --> Editor
    
    %% Track 3: Complex Project
    Router -- "Route: COMPLEX_PROJECT" --> Chief_Architect
    Chief_Architect -- "Propose Plan" --> WaitFor_Plan_Approval
    
    %% HITL Branch
    WaitFor_Plan_Approval -- "User Approves Plan" --> Site_Foreman
    WaitFor_Plan_Approval -- "User Requests Changes" --> Chief_Architect
    WaitFor_Plan_Approval -- "User Aborts Plan" --> Editor

    %% Execution Loop
    Site_Foreman -- "Execute Next Step" --> Worker_Complex
    Worker_Complex --> Project_Supervisor
    Project_Supervisor -- "Evaluate Outcome" --> After_Step_Router
    
    %% Outcome Routing
    After_Step_Router -- "Plan Complete" --> Editor
    After_Step_Router -- "Step Succeeded" --> Site_Foreman
    After_Step_Router -- "Step Failed (Correctable)" --> Site_Foreman
    After_Step_Router -- "Step Failed (Escalate)" --> Chief_Architect
    
    %% Final Output
    Editor -- "Provide Final Output" --> _end_
