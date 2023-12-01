import os
from flask import Flask, request
from flask_cors import CORS

import numpy as np
import json
import itertools

#from src.getDistance.getRealDistance import getRealDistance

from src.vrp_api import Heuristica


# Um bom tutorial: https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask-pt
app = Flask(__name__)
cors = CORS(app, resource={r"/*":{'origins': '*'}})


@app.route('/vrp', methods=['POST'])
def vrp():
    request_data = request.get_json()

    # Get Inputs

    I = Heuristica(request_data = request_data)
    #print(I.C_ij)
    I.exec()
    
    if not I.sucessReaded:
        json_object = json.dumps({"type":"error"}, indent=4)
        return json_object
    #print([I.routesSE.routes[s].route for s in I.S])

    two_routes = []
    t_cost = dict()
    
    t_time = dict()
    Ocupacao = dict()

    histogram = {
        "cost": [],
        "time": [],
        "ocup": []
        }
    for s in I.S:
        t_cost[str(s)] = float(I.routesSE.routes[s].tCost)
        histogram["cost"]+=[i for i in list(I.routesSE.routes[s].cost) if i > 0]

        t_time[str(s)] = float(I.calculate_distance(route = list(I.routesSE.routes[s].route), dist_matrix = I.t_ij))
        Ocupacao[str(s)] = []
        if len(I.routesSE.routes[s].route)>I.m_s[s]+1:
            _idx = 0
            for _i, idx in enumerate(I.routesSE.routes[s].idxEndRoute):
                if _i == 0:
                    route = I.routesSE.routes[s].route[:idx+1]
                else:
                    route = I.routesSE.routes[s].route[_idx:idx+1]
                _idx = idx
                if len(route)>2:
                    two_routes.append([int(i) for i in route])
                    OC = I.routesSE.routes[s].weight[_i] / I.routesSE.routes[s].cap
                    Ocupacao[str(s)].append(OC)
                    histogram["time"].append(float(I.calculate_distance(route = route, dist_matrix = I.t_ij)))
                    histogram["ocup"].append(OC*100)
                    
    ccc = lambda r, d: float(I.calculate_distance(route = list(r), dist_matrix = d))
    two_routes_time = {int(s):[] for s in I.S}
    two_routes_distance = {int(s):[] for s in I.S}
    for r in two_routes:
        two_routes_time[r[0]].append(ccc(r, I.ts_ij[r[0]]))
        two_routes_distance[r[0]].append(ccc(r, I.d_ij))
    # FIRST ECHELONG
    
    first_routes = []
    idx = 0
    
    r = list(I.routesFE.routes)
    for i in I.routesFE.idxEndRoute:
        if i > idx+1:
            first_routes.append([int(k) for k in r[idx:i]])
        idx = i
    
    #first_routes_distance = float(I.calculate_distance(route = list(I.routesFE.routes), dist_matrix = I.d_ij))
    #first_routes_time = float(I.calculate_distance(route = list(I.routesFE.routes), dist_matrix = I.t_ij))
    t_costFE = float(I.routesFE.tCost)
    """
    "first_routes": first_routes,
            "first_routes_time": first_routes_time,
            "first_routes_distance": first_routes_distance,
    """
    resp = {"type":"sucess",
            "two_routes": two_routes,
            "two_routes_time": two_routes_time,
            "two_routes_distance": two_routes_distance,
            "first_routes": first_routes,
            "t_cost": t_cost,
            "t_costFE": t_costFE,
            "t_time":t_time,
            "Ocupacao": Ocupacao,
            "histogram": histogram}
    json_object = json.dumps(resp, indent=4)
    return json_object



@app.route('/', methods=['POST', 'GET'])
def index():
    return "<h1>Hello World</h1>"







def main():
    port = int(os.environ.get("PORT", 5000)) # Pegar PORT do host
    app.run(debug=False, port = port)#host="0.0.0.0", 
    #app.run()

if __name__ == "__main__":
    main()
