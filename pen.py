import os,re
from collections import defaultdict
import networkx as nx
import numpy as np
from scipy.stats import skew
import argparse

extra_constraints={
    "TTCOMP-2002":False,
    "ITC-2007":True,
    "Harder-(Lewis and Paechter)":False,
    "Metaheuristics Network":False
}

def define_problem_formulation(dataset_path):
    problem_id=dataset_path.split(os.path.sep)[-1]

    if  re.match(r'^o\d+\.txt',problem_id):
        return "TTCOMP-2002"
    elif re.match(r"^big\_d+\.txt",problem_id):
        return "Harder-(Lewis and Paechter)"
    elif re.match(r"^easy\d+\.txt",problem_id):
        return "Metaheuristics Network"
    elif re.match(r"^i\d+\.txt",problem_id):
        return "ITC-2007"
    elif re.match(r"^hard\d+\.txt",problem_id):
        return "Metaheuristics Network"
    elif re.match(r"^med\_\d+\.txt",problem_id):
        return "Harder-(Lewis and Paechter)"
    elif re.match(r"^medium\d+\.txt",problem_id):
        return "Metaheuristics Network"
    
    return None

class Problem:
    def __init__(self,dataset_path:str):
        self.E=-1
        self.F=-1
        self.R=-1
        self.S=-1
        self.PPD=9
        self.D=5
        self.P=self.D*self.PPD
        self.events=None
        self.rooms=None
        self.period_availabilty=None
        self.event_available_rooms=None
        self.dataset_path=dataset_path
        self.formulation=define_problem_formulation(self.dataset_path)
        self.Graph=None
        
    def read_problem(self):
        self.rooms={room_id:{"F":set(),"C":-1} for room_id in range(self.R)}
        # - Each events has students list key->S Features set key->F and some higher priority events key->HPE
        self.events={event_id:{"S":set(),"F":set(),"HPE":list()} for event_id in range(self.E)}
        self.period_availabilty=defaultdict(list)
        self.event_available_rooms=defaultdict(list)
        
        with open(self.dataset_path,'r') as reader:
            line=reader.readline().strip()    
            self.E,self.R,self.F,self.S=[int(item) for item in line.split()]
            
            # 1. Begin with the room capacity and room creation
            for room_index in range(self.R):
                line=reader.readline().strip()
                self.rooms[room_index]={"F":list(),"C":int(line)}
            
            # 2. Event-Student relation
            for event_id in range(self.E):
                for student_id in range(self.S):
                    if int(reader.readline().strip())==1:
                        self.events[event_id]["S"].add(student_id)
            
            # 3. Room-Feature relation 
            for room_id in range(self.R):
                for feature_id in range(self.F):
                    if int(reader.readline().strip())==1:
                        self.rooms[room_id]["F"].add(feature_id)
            
            # 4. Event-Feature relation
            for event_id in range(self.E):
                for feature_id in range(self.F):
                    if int(reader.readline())==1:
                        self.events[event_id]["F"].add(feature_id)
            
            # Some formulations of the problem have some extra restrictions
            # such as event-period availability and some events have higher priority events
            # This is been determined by the problem formulation
            if extra_constraints[self.formulation]:
                # 5. Event-Period availability constraint
                for event_id in range(self.E):
                    for period_id in range(self.P):
                        line=reader.readline().strip()
                        if line=="":
                            break
                        if int(line)==1:
                            self.period_availabilty[event_id].append(period_id)
                
                # 6. Event-Event priority relations
                for event_id in range(self.E):
                    for event_id2 in range(self.E):
                        line=reader.readline().strip()
                        if line=="":
                            break
                        if event_id2<=event_id: continue
                        
                        if int(line)==1:
                            self.events[event_id]["HPE"].append(event_id2)
        
        # 7. Find available rooms for each one of the events
        for event_id in range(self.E):
            for room_id in range(self.R):
                if len(self.events[event_id]["S"])<self.rooms[room_id]["C"]: continue
                if self.events[event_id]["F"].issubset(self.rooms[room_id]["F"]):
                    self.event_available_rooms[event_id].append(room_id)
        
        # 8. Best best practice is to represent problem in Graph(networkx)
        self.Graph=nx.Graph()
        for event_id in range(self.E):
            for event_id2 in range(event_id+1,self.E):
                common_students=self.events[event_id]["S"].intersection(self.events[event_id2]["S"])
                if common_students>0:
                    self.Graph.add_edge(event_id,event_id2,weight=common_students)
    
    def statistics(self):
         # Calculated problem statistics
        # average_suitable_rooms_per_event=(1/∣E∣) * ​e∈E∑​-∣S(e)∣
        # average_room_size=(1/∣R∣) * r∈R-∑​cap(r)
        # conflict density= (2E+(E-1)/E),
        # average_event_period_unavailability(unavail(e)=P−avail(e)) =(1/E) * ​e∈E- ∑​unavail(e)  
        average_suitable_rooms_per_event=sum([len(self.event_available_rooms[event_id]) for event_id in range(self.E)])/self.E
        average_room_size=sum([self.rooms[room_id]["C"] for room_id in range(self.R)])/self.R
        conflict_density=nx.density(self.Graph)
        average_event_period_unavailability=sum(self.P-self.period_availabilty[event_id] for event_id in range(self.E))/self.E
        
        # Calculate conflict distribution
        degrees=dict(self.Graph.degree)
        degree_values=np.array(list(degrees.values()))
        degree_conflict=skew(degree_values)
        return average_suitable_rooms_per_event,average_room_size,conflict_density,average_event_period_unavailability,degree_conflict

if __name__=="__main__":
    problem=Problem("/Users/vasileios-nastos/Desktop/Post-enrollment-Timetabling/instances/o01.tim")     
    problem.read_problem()
    print(f"Statistics:{problem.statistics()}")                 