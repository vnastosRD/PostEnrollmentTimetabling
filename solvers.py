from ortools.sat.python import cp_model
from pen import Problem,extra_constraints
import os

def create_initial_solution(problem:Problem,timesol=600):
    model=cp_model.CpModel()
    xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f'{event_id}_{room_id}_{period_id}') for event_id in range(problem.E) for room_id in range(problem.R) for period_id in range(problem.P)}
    
    # 0. Add all the potential constraints in the problem
    for event_id in range(problem.E):
        model.add(
            sum([
                xvars[(event_id,room_id,period_id)]
                for room_id in range(problem.R)
                for period_id in range(problem.P)
            ])==1
        )
        
    # 1. Events should not be placed in in non valid rooms or periods
    for event_id in range(problem.E):
        for room_id in range(problem.R):
            if room_id not in problem.event_available_rooms[event_id]:
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)] for period_id in range(problem.P)
                    ])==0
                )
        
        if len(problem.period_availabilty[event_id])>0:
            for period_id in range(problem.P):
                model.add(
                    sum([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)])==0
                )
    
    # 2. In each period-room pair one or None events could be schedule but not >=2
    for room_id in range(problem.R):
        for period_id in range(problem.P):
            model.add(
                sum([xvars[(event_id,room_id,period_id)] for event_id in range(problem.E)])<=1
            )
    
    # 3. Events with common students could not be placed under the same period
    for event_id in range(problem.E):
        for neighbor_event in problem.Graph.neighbors(event_id):
            for period_id in range(problem.P):
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)] for room_id in range(problem.R)
                    ])+sum([
                        xvars[(neighbor_event,room_id,period_id)] for room_id in range(problem.R)
                    ])<=1
                )
    
    # 4. Add extra contraints to the solver if there are any 
    if extra_constraints[problem.formulation]:
        for event_id in range(problem.E):
            for event_id2 in problem.events[event_id]["HPE"]:
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)] * period_id
                        for room_id in problem.event_available_rooms[event_id]
                        for period_id in problem.period_availabilty[event_id]    
                    ])
                )<sum([
                    xvars[(event_id2,room_id,period_id)] * period_id
                    for room_id in problem.event_available_rooms[event_id2]
                    for period_id in problem.period_availabilty[event_id2]
                ])
    
    
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=timesol
    solver.parameters.num_search_workers=os.cpu_count()
    solver.parameters.log_search_progress=True
    status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter)
    solution={}
    if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
        for (event_id,room_id,period_id),decision_variable in xvars.items():
            if solver.Value(decision_variable)==1:
                solution[event_id]=(period_id,room_id)
    return solution

def solve_day_by_day(problem:Problem,day:int,solution_hints:dict):
    model=cp_model.CpModel()
    eset=[event_id for event_id,sol_params in solution_hints.items() if sol_params[0]>=day*problem.PPD and sol_params[0]<day*problem.PPD+problem.PPD]
    xvars={(event_id,room_id,period_id):model.NewBoolVar(f'{event_id}_{room_id}_{period_id}') for event_id in eset for room_id in range(problem.R) for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)}
    
    for event_id in range(problem.E):
        model.Add(
            sum([
                xvars[(event_id,room_id,period_id)]
                for room_id in range(problem.R)
                for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)
            ])==1
        )
    
    for event_id in eset:
        for room_id in range(problem.R):
            if room_id not in problem.event_available_rooms[event_id]:
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)
                    ])==0
                )
        
        for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD):
            if period_id not in problem.period_availabilty[event_id]:
                model.add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in range(problem.R)
                    ])==0
                )
        
    
if __name__=="__main__":
    dataset_path="/Users/vasileios-nastos/Desktop/Post-enrollment-Timetabling/instances/i08.tim"
    problem=Problem(dataset_path=dataset_path)
    print(f"Solution[{dataset_path.split(os.path.sep)[-1]}]:\n-----\n{create_initial_solution(problem,timesol=600)}")