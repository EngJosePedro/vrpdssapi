import os
from flask import Flask, request
from flask_cors import CORS
import geopy.distance # Usado para calcularDistancia

import numpy as np
import json

# Import componentes auxiliares de calculo
from src.data_analisys.funcoes_usadas_histograma import *
from src.data_analisys.funcoes_grafico_pizza import *

# Um bom tutorial: https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask-pt

app = Flask(__name__)

cors = CORS(app, resource={r"/*":{'origins': '*'}})

from src.VRP.Models.insercao import insercao
from src.VRP.Models.NearestNaborhood import NearestNaborhood
from src.VRP.Models.CLARKEWRIGHT import CLARKEWRIGHT



from src.Methods.ClarkeANDWright import ClarkeANDWright


def VRP_Data(request_data):
    dados = {
        "costumers": None,
        "satelites": None,
        "CD": None,
        "address": None,
        "ships": None,
        "TempoParada": None,
        "TempoParada_1E": None,
        "d1_ij": None,
        "d2_ij": None,
        "K1": None,
        "K2": None
    }
            
    if request_data:
        for dado in dados:
            if dado in request_data:
                dados[dado] = request_data[dado]
            else:
                return False, {"err": f"{dado} nao enviado"}
    else:
        return False, {"err": f"{dado} nao enviado"}
    
    return True, dados

def VRP_Data_Verif(request_data):
    dados = {
        "costumers": None,
        "satelites": None,
        "CD": None,
        "address": None,
        "ships": None,
        "TempoParada": None,
        "TempoParada_1E": None,
        "d1_ij": None,
        "d2_ij": None
    }
            
    if request_data:
        for dado in dados:
            if dado in request_data:
                dados[dado] = request_data[dado]
            else:
                return False, {"err": f"{dado} nao enviado"}
    else:
        return False, {"err": f"{dado} nao enviado"}

    a = dados["costumers"]
    b = dados["satelites"]
    c = dados["CD"]
    
    index_Dict = {
        cust["name"]: {
            "idx": idx,
            "index_aID": cust["index_aID"],
            "address": cust["address"]}
        for idx, cust in enumerate(a+b+c)}
    
    SAT = dados["satelites"][0]["name"]
    index_SAT = dados["satelites"][0]["index_aID"]

    CUSTOMER = lambda name, cID, address, index_aID, shID, addressLatLng, dropsize: {"name":name, "cID": cID, "address":address, "index_aID":index_aID, "shID":shID, "addressLatLng":addressLatLng, "dropsize":dropsize}
    CUSTOMERS = [
        CUSTOMER(C['name'], index_Dict[C['name']]["idx"], C['address'], C['index_aID'], C['shID'], C['addressLatLng'], C['dropsize'])
        for C in a
        ]

    Vehicle = dados["satelites"][0]["vehicle"]

    datas_to_RVP = [
        {"index_SAT": index_SAT, "CUSTOMERS": CUSTOMERS, "Vehicle": Vehicle}
        ]

    return True, dados, datas_to_RVP, index_Dict

from time import time

from numba import jit

class VRP:
    def __init__(self, instancia, index_Dict):
        self.costumers = instancia["costumers"]
        self.satelites = instancia["satelites"]
        self.CD = instancia["CD"]
        self.address = instancia["address"]
        self.address_list = list(self.address.keys())
        self.ships = instancia["ships"]
        self.TempoParada_2E = instancia["TempoParada"]
        self.TempoParada_1E = instancia["TempoParada_1E"]

        n = self.address_list

        a = self.costumers
        b = self.satelites
        c = self.CD

        n = len(a)+len(b)+len(c)
        
        self.index_Dict = index_Dict
        
        self.d = np.zeros(shape=(n, n)) - 1
        
        nA = len(self.address_list)
        self.d_address = np.zeros(shape=(nA, nA)) - 1
        self._tratar_D(instancia)
        self._dAddressToDCustomer()

    def _dAddressToDCustomer(self):
        for DADO_1 in self.index_Dict.values():
            idx_1 = DADO_1["idx"]
            index_aID_1 = DADO_1["index_aID"]
            address_1 = DADO_1["address"]
            for DADO_2 in self.index_Dict.values():
                idx_2 = DADO_2["idx"]
                index_aID_2 = DADO_2["index_aID"]
                address_2 = DADO_2["address"]

                if self.d_address[index_aID_1, index_aID_2] >= 0:
                    self.d[idx_1, idx_2] = self.d_address[index_aID_1, index_aID_2]
            #print(DADO)
        pass
    
    def _tratar_D2(self, instancia):
        
        d1 = instancia["d1_ij"]
        d2 = instancia["d2_ij"]

        def f(ad2):
            def filtro(dado):
                return dado[0] == ad2
            return filtro
            
        def data(key1, key2):
            idx_1 = self.index_Dict[key1]["idx"]
            index_aID_1 = self.index_Dict[key1]["index_aID"]
            address_1 = self.index_Dict[key1]["address"]

            idx_2 = self.index_Dict[key2]["idx"]
            index_aID_2 = self.index_Dict[key2]["index_aID"]
            address_2 = self.index_Dict[key2]["address"]
            
            return idx_1, index_aID_1, address_1, idx_2, index_aID_2, address_2
            
        #@jit(nopython=True, parallel=True)

        _KEYS = list(self.index_Dict.keys())

        idxList = [ [k,self.index_Dict[k]["idx"],self.index_Dict[k]["address"] ]  for k in self.index_Dict]
        def filterFunction(d_List):
            def filter(lista):
                addressCliente = lista[2]
                return addressCliente in d_List
            return filter
                           
                            
        
        for key1 in _KEYS:
            #print("key1", key1)
            for key2 in _KEYS:
                if key1 != key2:
                    idx_1, index_aID_1, address_1, idx_2, index_aID_2, address_2 = data(key1, key2)
                    
                    if address_1 in d1:
                        for data2 in filter(f(address_2), d1[address_1]):
                            d = data2[1]
                            self.d[idx_1, idx_2] = d
                    if address_1 in d2:
                        for data2 in filter(f(address_2), d2[address_1]):
                            d = data2[1]
                            self.d[idx_1, idx_2] = d
        
                    
    def _tratar_D(self, instancia):

        d1 = instancia["d1_ij"]
        d2 = instancia["d2_ij"]
        
        for idx_1, key1 in enumerate(self.address_list):
            if key1 in d1:
                
                for data2 in d1[key1]:
                    key2 = data2[0]
                    d = data2[1]
                    idx_2 = data2[2]
                    
                    self.d[idx_1, idx_2] = d
            if key1 in d2:
                for data2 in d2[key1]:
                    key2 = data2[0]
                    d = data2[1]
                    idx_2 = data2[2]

                    self.d_address[idx_1, idx_2] = d
        
class Algothm(VRP):
    def main(self):
        pass
@app.route('/TESTE', methods=['POST'])
def TESTE():
    request_data = request.get_json()
    print("setup")
    sucess, dados, datas_to_RVP, index_Dict = VRP_Data_Verif(request_data)
    print("setup - distance")
    d = VRP(dados, index_Dict).d
    
    print("fim setup")
    Heuristic = ClarkeANDWright()

    index_SAT = datas_to_RVP[0]["index_SAT"]
    Vehicle = datas_to_RVP[0]["Vehicle"]
    CUSTOMERS = datas_to_RVP[0]["CUSTOMERS"]

    Heuristic.main(d, index_SAT, Vehicle, CUSTOMERS)
    datas_to_RVP[0]["routes"]=Heuristic.routes
    #t = time()
    #VRP_ = Algothm(dados)
    #VRP_.main()
    #print("T_Setup", time()-t)
    
    json_object = json.dumps(datas_to_RVP, indent=4)
    
    return json_object




@app.route('/VRP_Insertion', methods=['POST'])
def VRP_Insertion():
    request_data = request.get_json()
    
    sucess, dados = VRP_Data(request_data)
    
    if sucess:
        VRP = insercao(dados)
        
        if len(VRP.S)>0:
            VRP.Rotas_SegundaCamada()
        VRP.Rotas_PrimeiraCamada()
        
        dados["d1_ij"] = VRP.d1_ij
        dados["d2_ij"] = VRP.d2_ij
        dados["rotas_2E"] = VRP.rotas_2E
        dados["rotas_1E"] = VRP.rotas_1E
    
        dados["ships"] = {ship: r["fromSat"] for r in VRP.rotas_2E for ship in r["ships"]}
        dados["ships"].update({ship: r["fromSat"] for r in VRP.rotas_1E for ship in r["ships"] if ship in VRP.R})
    
    
    json_object = json.dumps(dados, indent=4)
    
    return json_object

@app.route('/VRP_NearestNaborhood', methods=['POST'])
def VRP_NearestNaborhood():
    request_data = request.get_json()
    
    sucess, dados = VRP_Data(request_data)
    
    if sucess:
        VRP = NearestNaborhood(dados)
        
        if len(VRP.S)>0:
            VRP.Rotas_SegundaCamada()
        VRP.Rotas_PrimeiraCamada()

    dados["d1_ij"] = VRP.d1_ij
    dados["d2_ij"] = VRP.d2_ij
    dados["rotas_2E"] = VRP.rotas_2E
    dados["rotas_1E"] = VRP.rotas_1E
    
    dados["ships"] = {ship: r["fromSat"] for r in VRP.rotas_2E for ship in r["ships"]}
    dados["ships"].update({ship: r["fromSat"] for r in VRP.rotas_1E for ship in r["ships"] if ship in VRP.R})
    
    json_object = json.dumps(dados, indent=4)
    
    return json_object


@app.route('/VRP_CLARKEWRIGHT', methods=['POST'])
def VRP_CLARKEWRIGHT():
    request_data = request.get_json()
    dados = {
    "costumers": None,
    "satelites": None,
    "CD": None,
    "address": None,
    "ships": None,
    "TempoParada": None,
    "d1_ij": None,
    "d2_ij": None,
    "K1": None,
    "K2": None
    }
    
    
    if request_data:
        for dado in dados:
            if dado in request_data:
                dados[dado] = request_data[dado]
            else:
                return {"err": f"{dado} nao enviado"}

    VRP = CLARKEWRIGHT(dados)
    VRP.Rotas_SegundaCamada()

    dados["d1_ij"] = VRP.d1_ij
    dados["d2_ij"] = VRP.d2_ij
    dados["rotas"] = VRP.rotas
    
    dados["ships"] = {ship: r["fromSat"] for r in VRP.rotas for ship in r["ships"]}
    
    json_object = json.dumps(dados, indent=4)
    
    return json_object












@app.route('/', methods=['POST', 'GET'])
def index():
    return "<h1>Hello World</h1>"




















# Usando dados de JSON


# Clustering method
@app.route('/Clustering_Capacited_nearest_neighbor', methods=['POST'])
def Clustering_Capacited_nearest_neighbor():
    request_data = request.get_json()
    costumers = None
    satellities = None
    
    if request_data:
        if "costumers" in request_data:
            costumers = request_data["costumers"]
        if "satellities" in request_data:
            satellities = request_data["satellities"]
    return {"satellities": satellities}
# Vehicle Routiong Problem
@app.route('/Capacited_nearest_neighbor', methods=['POST'])
def Capacited_nearest_neighbor():
    request_data = request.get_json()
    vehicle = None
    locais = None
    
    rotas = []
    
    if request_data:
        if "vehicle" in request_data:
            vehicle = request_data["vehicle"][0]
        if "locais" in request_data:
            locais = request_data["locais"]
    if vehicle!=None and locais != None:
        cds = []
        customers = []
        
        for loc in locais:
            if loc["type"]=="warehouse":
                cds.append(loc)
            elif loc["type"]=="customer":
                customers.append(loc)
        
        D = calc_Dists_KM(locais)
        
        
        clientes_Alocados = []
        i = 0
    
        while len(clientes_Alocados) < len(customers):
            rota_V_i = [cds[0]["id"]]
            rotaFinalizada = False
            capacidade_Disponivel = vehicle["capacidade"]
            
            while not rotaFinalizada:
                cliente_Adicionado_Na_Rota = -1
                menor_Dist = -1
                demanda = -1
                for customer in customers:
                    if customer['id'] not in clientes_Alocados and customer["data"]["demand"] <= capacidade_Disponivel:
                        if menor_Dist == -1 or D[str(rota_V_i[-1])][str(customer['id'])] < menor_Dist:
                            menor_Dist = D[str(rota_V_i[-1])][str(customer['id'])]
                            cliente_Adicionado_Na_Rota = customer['id']
                            demanda = customer["data"]["demand"]
                if cliente_Adicionado_Na_Rota == -1:
                    rotaFinalizada = True
                else:
                    rota_V_i.append(cliente_Adicionado_Na_Rota)
                    clientes_Alocados.append(cliente_Adicionado_Na_Rota)
                    capacidade_Disponivel -= demanda
            rota_V_i.append(cds[0]["id"])
            if len(rota_V_i)>2:
                rotas.append({"id":i, "waypoints": rota_V_i})
                i+=1
            else:
                break
            
    routes = {"routes":rotas, "D": D}
    return routes



    
def calc_Dists_KM(locais):
    D = dict()#primeiro indice origem segundo indice destino
    
    for loc1 in locais:
        D[str(loc1["id"])] = dict()
        for loc2 in locais:
            coords_1 = (loc1["coordinates"][0], loc1["coordinates"][1])
            coords_2 = (loc2["coordinates"][0], loc2["coordinates"][1])
            
            D[str(loc1["id"])][str(loc2["id"])] = geopy.distance.geodesic(coords_1, coords_2).km
    return D

def main():
    port = int(os.environ.get("PORT", 5000)) # Pegar PORT do host
    app.run(debug=False, port = port)#host="0.0.0.0", 
    #app.run()

if __name__ == "__main__":
    main()
