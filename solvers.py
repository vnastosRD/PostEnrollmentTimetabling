from ortools.sat.python import cp_model
from pen import Problem,extra_constraints
from itertools import combinations
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

def solve_day_by_day(problem:Problem,day:int,solution_hints:dict,timesol:int):
    # Try to optimize each day seperatly
    event_set=[event_id for event_id,(period_id,_) in solution_hints.items() if period_id>=day*problem.PPD and period_id<day*problem.PPD+problem.PPD]
    model=cp_model.CpModel()
    xvars={(event_id,room_id,period_id):model.NewBoolVar(name=f"{event_id}_{room_id}_{period_id}") for event_id in event_set for room_id in problem.event_available_rooms[event_id] for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)}
    day_event_combinations=[frozenset(ecombination) for ecombination in combinations(event_set,3) if frozenset(ecombination) in problem.event_combinations]

    for event_id in event_set:
        model.AddExactlyOne([xvars[(event_id,room_id,period_id)] for room_id in range(problem.R) for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)])
    
    for event_id in event_set:
        for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD):
            if period_id not in problem.period_availabilty[event_id]:
                model.Add(
                    sum([
                        xvars[(event_id,room_id,period_id)]
                        for room_id in problem.event_available_rooms[event_id]
                        for period_id in range(problem.PPD)
                    ])==0
                )
    
    for room_id in range(problem.R):
        for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD):
            model.AddAtMostOne([xvars[(event_id,room_id,period_id)] for event_id in event_set if room_id in problem.event_available_rooms[event_id]])

    for event_id in event_set:
        for event_id2 in problem.Graph.neighbors(event_id):
            if event_id2 in event_set:
                for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD):
                    if period_id in problem.period_availabilty[event_id] and period_id in problem.period_availabilty[event_id2]:
                        neighbored_events=[xvars[(event_id,room_id,period_id)] for room_id in problem.event_available_rooms[event_id]]
                        neighbored_events.extend([xvars[(event_id2,room_id,period_id)] for room_id in problem.event_available_rooms[event_id2]])
                        model.AddAtMostOne(neighbored_events)

    if extra_constraints[problem.formulation]:
        for event_id in event_set:
            for event_id2 in problem.events[event_id]["HPE"]:
                if event_id2 in event_set:
                    model.Add(
                        sum([
                            xvars[(event_id,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)
                        ])<sum([
                            xvars[(event_id2,room_id,period_id)]*period_id
                            for room_id in range(problem.R)
                            for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD)
                        ])
                    )
    # Calculate Penalty
    consecutive_events={ecombination:model.NewBoolVar(name=f'{"_".join([str(ecomb_iter_name) for ecomb_iter_name in ecombination])}') for ecombination in day_event_combinations}
    for ecombination in day_event_combinations.keys():
        for period_id in range(day*problem.PPD,day*problem.PPD+problem.PPD-3):
            model.Add(
                sum([
                    xvars[(event_id,room_id,partial_period_id)]
                    for event_id in ecombination
                    for room_id in range(problem.R)
                    for partial_period_id in range(period_id,period_id+3)
                ])<=2+consecutive_events[ecombination]
            )

    objective=[
        sum([consecutive_events[event_combination_iter]*problem.event_combinations[event_combination_iter] for event_combination_iter in day_event_combinations]),
        sum([xvars[(event_id,room_id,day*problem.PPD+problem.PPD-1)] for event_id in event_set for room_id in range(problem.R)])
    ]

    model.Minimize(sum(objective))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=timesol
    solver.parameters.num_search_workers=os.cpu_count()
    solver.parameters.log_search_progress=True
    status=solver.Solve(model=model,solution_callback=cp_model.ObjectiveSolutionPrinter())
    
    if status in [cp_model.FEASIBLE,cp_model.OPTIMAL]:
        solution={}
        for (event_id,room_id,period_id),decision_variable in xvars.items():
            if solver.Value(decision_variable)==1:
                solution[event_id]=(period_id,room_id)
        return solution
    return None
    
if __name__=="__main__":
    dataset_path="/Users/vasileios-nastos/Desktop/Post-enrollment-Timetabling/instances/i08.tim"
    problem=Problem(dataset_path=dataset_path)
    print(f"Solution[{dataset_path.split(os.path.sep)[-1]}]:\n-----\n{create_initial_solution(problem,timesol=600)}")