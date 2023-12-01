import os
from flask import Flask, request
from flask_cors import CORS

import numpy as np
import json
import itertools

from src.getDistance.getRealDistance import getRealDistance

# Um bom tutorial: https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask-pt
app = Flask(__name__)
cors = CORS(app, resource={r"/*":{'origins': '*'}})


@app.route('/getDistance', methods=['GET'])
def getDistance():

    queryPoints = "point=-23.529494679800447,-46.779143346973925&point=-23.56028743222669,-46.68386828225753&point=-23.529494679800447,-46.779143346973925&point=-23.52167603127064,-46.70137549891982"
    queryInstructions = "true"
    queryType = "json"
    queryKey = "e391ea04-e80d-4727-b35c-a66842706a30"
    queryVehicle = "bike"
    url = f"https://graphhopper.com/api/1/route?{queryPoints}&instructions={queryInstructions}&type={queryType}&key={queryKey}&vehicle={queryVehicle}"
    print(url)
    
    status, data = getRealDistance(url)

    if status == 200:
        json_object = json.dumps(data, indent=4)
        return json_object

    json_object = json.dumps({"type":"error", "status":status}, indent=4)
    return json_object



@app.route('/get', methods=["GET"])
def get():
    waypoints = request.args.get('waypoints')
    print(waypoints)
    return getDistance()


@app.route('/getDistanceMatrix', methods=['POST'])
def getDistanceMatrix():
    request_data = request.get_json()

    # Get Inputs
    nodes = []
    vehicle = "car"
    if request_data:
        for inp in request_data:
            if inp == "nodes":
                nodes = request_data[inp]
            if inp == "vehicle":
                vehicle = request_data[inp]
        if nodes==[]:
            json_object = json.dumps({"type":"error", "status": 400, "msg": "Invalid Data"}, indent=4)
            return json_object
    else:
        json_object = json.dumps({"type":"error", "status": 400, "msg": "Withot json Data"}, indent=4)
        return json_object

    dists = np.zeros(shape=(len(nodes), len(nodes)))
    times = np.zeros(shape=(len(nodes), len(nodes)))

    arcs = list(itertools.permutations(range(len(nodes)), 2))
    print("Qnt Arcs", len(arcs))
    
    
    def getArcs(arcs, qntNodesPerRequest=2):
        if len(arcs)<0:
            return [], []
        elif len(arcs) < qntNodesPerRequest:
            return arcs, []
        # Arcos a serem trabanhados
        rArcs = arcs[:qntNodesPerRequest]
        # Arcos consequencia -> intercecao entre arcos
        dummy = [() if i==0 else (rArcs[i-1][1], a[0]) for i, a in enumerate(rArcs)]
        #print("dummy", dummy)
        # Remover arcos trabalhados
        for arc in rArcs + dummy:
            if arc not in arcs:
                continue
            arcs.remove(arc)
            #print(arc)
            
        return rArcs, arcs
    def getURL(rArcs, vehicle):

        point = lambda node: f"point={node['lat']},{node['lng']}"
        points = lambda arcs: [point(nodes[i]) for arc in arcs for i in arc]
        
        queryPoints = "&".join(points(rArcs)) #"point=-23.529494679800447,-46.779143346973925&point=-23.56028743222669,-46.68386828225753&point=-23.529494679800447,-46.779143346973925&point=-23.52167603127064,-46.70137549891982"
        queryInstructions = "true"
        queryType = "json"
        queryKey = "e391ea04-e80d-4727-b35c-a66842706a30"
        queryVehicle = vehicle
        url = f"https://graphhopper.com/api/1/route?{queryPoints}&instructions={queryInstructions}&type={queryType}&key={queryKey}&vehicle={queryVehicle}"
        return url
    def getD(respData):
        D=[]
        T=[]
        dist = 0
        time = 0
        contWaypoint = 1
        for path in respData["paths"]:
            for instruction in path["instructions"]:
                dist += instruction["distance"]
                time += instruction["time"]
                if instruction["text"]==f"Waypoint {contWaypoint}" or instruction["text"]=="Arrive at destination":
                    contWaypoint+=1
                    D.append(dist)
                    T.append(time)
                    dist = 0
                    time = 0
            #print(len(path))
            #print(D)
            #print(T)
            break
        return D, T
    def saveData(D, T, dists, times, rArcs):
        n = len(D)
        i = -1
        j = -1
        for idx in range(n):
            # se idx é par, int(idx/2) é o arco atendido
            if idx%2==0:
                idxArc = int(idx/2)
                i = rArcs[idxArc][0]
                j = rArcs[idxArc][1]
            else:# Caso contrario, a viajem é entre o to do nó anterior e o from do sucessor
                idxArc = int(idx/2) + 1
                i = rArcs[idxArc-1][1]
                j = rArcs[idxArc][0]
            if i!=-1 and j!=-1:
                dists[i,j] = D[idx]
                times[i,j] = T[idx]
        return dists, times
    #listResps=[]
    while len(arcs):
        rArcs, NEWarcs = getArcs(arcs.copy())
        url = getURL(rArcs, vehicle)
        status, data = getRealDistance(url)
        if status==200:
            arcs = NEWarcs
            D, T = getD(data)
            dists, times = saveData(D, T, dists, times, rArcs)
            #listResps.append(data)

    dists = [list(dists[i]) for i in range(len(nodes))]
    times = [list(times[i]) for i in range(len(nodes))]
    resp = {"dists": dists, "times":times}#, "resps":listResps}
    json_object = json.dumps(resp, indent=4)
    return json_object

@app.route('/getDistanceRoutes', methods=['POST'])
def getDistanceRoutes():
    request_data = request.get_json()

    # Get Inputs
    nodes = []
    vehicle = "car"
    if request_data:
        for inp in request_data:
            if inp == "nodes":
                nodes = request_data[inp]
            if inp == "vehicle":
                vehicle = request_data[inp]
        if nodes==[]:
            json_object = json.dumps({"type":"error", "status": 400, "msg": "Invalid Data"}, indent=4)
            return json_object
    else:
        json_object = json.dumps({"type":"error", "status": 400, "msg": "Withot json Data"}, indent=4)
        return json_object

    arcs = list(itertools.permutations(range(len(nodes)), 2))
    print("Qnt Arcs", len(arcs))
    
    def getArcs(arcs, qntNodesPerRequest=2):
        if len(arcs)<0:
            return [], []
        elif len(arcs) < qntNodesPerRequest:
            return arcs, []
        # Arcos a serem trabanhados
        rArcs = arcs[:qntNodesPerRequest]
        # Arcos consequencia -> intercecao entre arcos
        dummy = [() if i==0 else (rArcs[i-1][1], a[0]) for i, a in enumerate(rArcs)]
        #print("dummy", dummy)
        # Remover arcos trabalhados
        for arc in rArcs + dummy:
            if arc not in arcs:
                continue
            arcs.remove(arc)
            #print(arc)
            
        return rArcs, arcs
    def getURL(rArcs, vehicle):

        point = lambda node: f"point={node['lat']},{node['lng']}"
        points = lambda arcs: [point(nodes[i]) for arc in arcs for i in arc]
        
        queryPoints = "&".join(points(rArcs)) #"point=-23.529494679800447,-46.779143346973925&point=-23.56028743222669,-46.68386828225753&point=-23.529494679800447,-46.779143346973925&point=-23.52167603127064,-46.70137549891982"
        queryInstructions = "true"
        queryType = "json"
        queryKey = "e391ea04-e80d-4727-b35c-a66842706a30"
        queryVehicle = vehicle
        url = f"https://graphhopper.com/api/1/route?{queryPoints}&instructions={queryInstructions}&type={queryType}&key={queryKey}&vehicle={queryVehicle}"
        return url
    
    listResps=[]
    while len(arcs):
        rArcs, NEWarcs = getArcs(arcs.copy())
        url = getURL(rArcs, vehicle)
        status, data = getRealDistance(url)
        if status==200:
            arcs = NEWarcs
            listResps.append({"rArcs": rArcs, "paths": data["paths"]})

    resp = {"resps": listResps}
    json_object = json.dumps(resp, indent=4)
    return json_object

@app.route('/getDistanceMatrixFromPaths', methods=['POST'])
def getDistanceMatrixFromPaths():
    request_data = request.get_json()

    # Get Inputs
    resps = []
    nN = -1
    if request_data:
        for inp in request_data:
            if inp == "resps":
                resps = request_data[inp]
            if inp == "nN":
                nN = request_data[inp]
        if resps==[] or nN==-1:
            json_object = json.dumps({"type":"error", "status": 400, "msg": "Invalid Data"}, indent=4)
            return json_object
    else:
        json_object = json.dumps({"type":"error", "status": 400, "msg": "Withot json Data"}, indent=4)
        return json_object

    dists = np.zeros(shape=(nN, nN))
    times = np.zeros(shape=(nN, nN))

    def getD(respData):
        D=[]
        T=[]
        dist = 0
        time = 0
        contWaypoint = 1
        for path in respData["paths"]:
            for instruction in path["instructions"]:
                dist += instruction["distance"]
                time += instruction["time"]
                if instruction["text"]==f"Waypoint {contWaypoint}" or instruction["text"]=="Arrive at destination":
                    contWaypoint+=1
                    D.append(dist)
                    T.append(time)
                    dist = 0
                    time = 0
            #print(len(path))
            #print(D)
            #print(T)
            break
        return D, T
    def saveData(D, T, dists, times, rArcs):
        n = len(D)
        i = -1
        j = -1
        for idx in range(n):
            # se idx é par, int(idx/2) é o arco atendido
            if idx%2==0:
                idxArc = int(idx/2)
                i = rArcs[idxArc][0]
                j = rArcs[idxArc][1]
            else:# Caso contrario, a viajem é entre o to do nó anterior e o from do sucessor
                idxArc = int(idx/2) + 1
                i = rArcs[idxArc-1][1]
                j = rArcs[idxArc][0]
            if i!=-1 and j!=-1:
                dists[i,j] = D[idx]
                times[i,j] = T[idx]
        return dists, times
    
    for resp in resps:
        rArcs=resp["rArcs"]
        #paths=resp["paths"]
        D, T = getD({"paths": resp["paths"]})
        dists, times = saveData(D, T, dists, times, rArcs)
    dists = [list(dists[i]) for i in range(len(nodes))]
    times = [list(times[i]) for i in range(len(nodes))]
    resp = {"dists": dists, "times":times}#, "resps":listResps}
    json_object = json.dumps(resp, indent=4)
    return json_object




@app.route('/', methods=['POST', 'GET'])
def index():
    return "<h1>Hello World</h1>"

import time

def translate(paths):
    distances = []
    times = []
    d = 0
    t = 0
    
    for i, instruction in enumerate(paths[0]["instructions"]):
        if ("Waypoint " in instruction["text"] or "Arrive at destination" in instruction["text"]):
            distances.append(d)
            times.append(t)
            d = 0
            t = 0
        #print(instruction["text"])
        d += instruction["distance"]
        t = instruction["time"]
    return distances, times
def teste():
    t = time.time()
    file = r"SETUP\DistanceMatrix\address.json"
    with open(file, "r") as user_file:
        file_contents = user_file.read()
        user_file.close() 
    parsed_json = json.loads(file_contents)

    
    
    waypoint = lambda aID: "point={},{}".format(parsed_json[aID]['lat'], parsed_json[aID]["lng"]) 
    aIDs = list(parsed_json.keys())

    d_ij = np.zeros(shape=(len(aIDs), len(aIDs)))
    t_ij = np.zeros(shape=(len(aIDs), len(aIDs)))

    print(time.time()-t)
    t = time.time()
    

    nP = 5
    waypoints = [i for i in range(len(aIDs)) if i < nP]
    queryPoints = "&".join([waypoint(aIDs[i]) for i in waypoints])
    queryInstructions = "true"
    queryType = "json"
    queryKey = "e391ea04-e80d-4727-b35c-a66842706a30"
    queryVehicle = "bike"
    url = f"https://graphhopper.com/api/1/route?{queryPoints}&instructions={queryInstructions}&type={queryType}&key={queryKey}&vehicle={queryVehicle}"

    print(time.time()-t)
    t = time.time()
    status, data = getRealDistance(url)
    print(time.time()-t)
    t = time.time()
    print(waypoints)
    if status == 200:
        distances, times = translate(data["paths"])
        print(distances)
        
    print(time.time()-t)
    t = time.time()
        
teste()


    




def main():
    port = int(os.environ.get("PORT", 5000)) # Pegar PORT do host
    app.run(debug=False, port = port)#host="0.0.0.0", 
    #app.run()

if __name__ == "__main__":
    main()
