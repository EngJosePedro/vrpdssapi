import numpy as np
import json
import itertools
from srcTeste.MP import MP
from srcTeste.MYrequest import MYrequest
from src.getDistance.getRealDistance import getRealDistance

from srcTeste.getRef import getRef

import time
keys = ["34847c15-fb36-436a-aa39-d824540c952c","6977925f-018c-4cd0-944d-a39c3835316d", "661640f2-70d9-4e0f-ac20-f79223969d80"]     
idx = 2
def make_api_request(data):
    
    return MYrequest(data, getRealDistance)#, key=keys[idx]

#RESPOSTAS = []



ArcsEstudados = []

def tratamento(resps, input_data, d_ij, t_ij):
    
    for c, resp in enumerate(resps):
        ref = input_data[c]
        #print(ref)
        if len(resp[0])>0:
            dist = resp[0]
            tempo = resp[1]
            
            for i in range(len(ref)-1):
                #print(ref[i], ref[i+1], dist[i])
                d_ij[ref[i], ref[i+1]] = dist[i]
                t_ij[ref[i], ref[i+1]] = tempo[i]
        else:
            #Erro
            print("Falha")
            for i in range(len(ref)-1):
                try:
                    ArcsEstudados.remove((ref[i], ref[i+1]))
                except:
                    print("Erro")
    #print(d_ij)
    return d_ij, t_ij
d = None
t = None
"""try:
    with open("r.txt", "r") as f:
        data = "".join(f.readlines())
        data = data.replace("\n", "")
        data = list(data)
        print(data)
        d = data[0]
        t = data[1]
except:
    pass"""

t = time.time()   
if __name__ == '__main__':
    # Lista de dados de entrada para a API
    
    try:
        #file = r"SETUP\DistanceMatrix\address.json"
        file = "nodes.json"
        with open(file, "r") as user_file:
            file_contents = user_file.read()
            user_file.close() 
        nodes = json.loads(file_contents)
        address = dict()
        
        for i, node in enumerate(nodes):
            latlng = (node["latlng"]["lat"], node["latlng"]["lng"])
            if latlng not in address:
                address[latlng] = list()
            address[latlng].append(i)
        latlngs = list(address.keys())

        pointGraphHouper = lambda latlng: "point={},{}".format(latlng[0], latlng[1]) 
        pointsGraphHouper = lambda LL: "&".join(pointGraphHouper(latlngs[i]) for i in LL)
        pointOSRM = lambda latlng: "{},{}".format(latlng[1], latlng[0]) 
        pointsOSRM = lambda LL: ";".join(pointOSRM(latlngs[i]) for i in LL)

        modo = "OSRM"
        points = lambda LL: pointsOSRM(LL) if modo == "OSRM" else pointsGraphHouper(LL)
        
        if d == None:
            d_ij = np.zeros(shape=(len(latlngs), len(latlngs)))
            t_ij = np.zeros(shape=(len(latlngs), len(latlngs)))
        else:
            d_ij = np.array(d)
            t_ij = np.array(t)
        
        
        ref = [-1]
        input_data = []
        refs = []
        nP = 10
        
        while len(ref):
            ref, ArcsEstudados = getRef(latlngs, ArcsEstudados.copy(), ref = [], n=70)
            
            if len(ref)==0: continue
            #print(ref)
            input_data.append(points(ref))
            refs.append(ref)
            
            if len(input_data)>=nP:
                
                resps = MP(input_data, make_api_request)
                d_ij, t_ij = tratamento(resps, refs, d_ij, t_ij)
                unique, counts = np.unique(d_ij, return_counts=True)

                teste = dict(zip(unique, counts))
                if 0 in unique:
                    print(len(latlngs) * len(latlngs) - len(latlngs) , teste[0] , len(latlngs)*len(latlngs) - teste[0] - len(latlngs),time.time() - t)
                #RESPOSTAS.append(resps)
                input_data = []
                refs = []
                time.sleep(0.5)
                
        if len(input_data)>0:
                resps = MP(input_data, make_api_request)
                d_ij, t_ij = tratamento(resps, refs, d_ij, t_ij)
                
                

                #RESPOSTAS.append(resps)
                input_data = []
                refs = []
            
        #for result in RESPOSTAS:
        #    print(result)

        #with open("rResp.txt", "w") as f:
        #    f.write(str(RESPOSTAS))
        with open("r.txt", "w") as f:
            f.write(str([[list(d_ij[i]) for i in range(len(latlngs))], [list(t_ij[i]) for i in range(len(latlngs))]]))
            
    except KeyboardInterrupt:
        #with open("rResp.txt", "w") as f:
        #    f.write(str(RESPOSTAS))
        with open("r.txt", "w") as f:
            f.write(str([[list(d_ij[i]) for i in range(len(latlngs))], [list(t_ij[i]) for i in range(len(latlngs))]]))

