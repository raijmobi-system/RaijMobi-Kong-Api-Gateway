# import requests
# import uuid
# import random
# import time
# import json
# from datetime import datetime, timedelta, timezone

# BASE_URL = "http://localhost:8000"
# RIDE_SERVICE_URL = "http://localhost:8004"  # porta interna do ride-service

# # ------------------------------------------------------------
# # Utilitários
# # ------------------------------------------------------------
# def gerar_cpf():
#     def digito(digs):
#         s = sum(d * (len(digs)+1 - i) for i, d in enumerate(digs))
#         d = 11 - (s % 11)
#         return d if d < 10 else 0
#     base = [random.randint(0, 9) for _ in range(9)]
#     base.append(digito(base))
#     base.append(digito(base))
#     cpf_str = ''.join(map(str, base))
#     return f'{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}'

# def random_email():
#     return f"test_{uuid.uuid4().hex[:8]}@example.com"

# def check_response(resp, success_code=200):
#     if resp.status_code != success_code:
#         print(f"❌ Erro {resp.status_code}: {resp.text[:200]}")
#         resp.raise_for_status()
#     return resp.json()

# def get_tokens(email, password):
#     resp = requests.post(f"{BASE_URL}/api/login/", data={"email": email, "password": password})
#     data = check_response(resp)
#     return data["access"], data["refresh"]

# def auth_header(token):
#     return {"Authorization": f"Bearer {token}"}

# # Função de requisição com log detalhado
# def req(method, url, **kwargs):
#     headers = kwargs.get("headers")
#     masked_headers = None
#     if headers and "Authorization" in headers:
#         token = headers["Authorization"].split()[1]
#         masked = token[:10] + "..." + token[-10:] if len(token) > 20 else token
#         masked_headers = {"Authorization": f"Bearer {masked}"}
#     else:
#         masked_headers = headers

#     body = None
#     if "data" in kwargs:
#         body = kwargs["data"]
#     elif "json" in kwargs:
#         body = kwargs["json"]

#     print(f"\n➡️ {method} {url}")
#     if masked_headers:
#         print(f"   headers: {json.dumps(masked_headers, indent=2)}")
#     if body:
#         print(f"   body:\n{json.dumps(body, indent=2, ensure_ascii=False)}")
    
#     resp = requests.request(method, url, **kwargs)
#     print(f"⬅️ {resp.status_code}")
#     return resp

# # ------------------------------------------------------------
# # 1. Registrar usuários
# # ------------------------------------------------------------
# driver_email = random_email()
# passenger_email = random_email()
# password = "Teste@123"

# print("\n📝 Registrando motorista...")
# resp = req("POST", f"{BASE_URL}/api/register/", data={
#     "email": driver_email, "nome": "Motorista Silva", "password": password,
#     "cpf": gerar_cpf(), "telefone": "11999990001", "tipo_usuario": "Motorista",
# })
# driver_data = check_response(resp, 201)
# print(f"✅ Motorista registrado:\n{json.dumps(driver_data, indent=2)}")

# print("\n📝 Registrando passageiro...")
# resp = req("POST", f"{BASE_URL}/api/register/", data={
#     "email": passenger_email, "nome": "Passageiro Santos", "password": password,
#     "cpf": gerar_cpf(), "telefone": "11999990002", "tipo_usuario": "Passageiro",
# })
# passenger_data = check_response(resp, 201)
# print(f"✅ Passageiro registrado:\n{json.dumps(passenger_data, indent=2)}")

# print("\n⏳ Aguardando sincronização Kafka (9s)...")
# time.sleep(9)

# # ------------------------------------------------------------
# # 2. Login
# # ------------------------------------------------------------
# print("\n🔐 Fazendo login...")
# driver_access, driver_refresh = get_tokens(driver_email, password)
# passenger_access, passenger_refresh = get_tokens(passenger_email, password)
# print("✅ Tokens obtidos")

# # ------------------------------------------------------------
# # Sincronização manual do motorista DIRETAMENTE no ride-service
# # ------------------------------------------------------------
# print("\n👤 Sincronizando motorista no ride-service (porta 8004)...")
# sync_payload = {
#     "id": driver_data["id"],
#     "name": driver_data["nome"],
#     "is_driver": True
# }
# resp = requests.post(f"{RIDE_SERVICE_URL}/api/ride/users/", json=sync_payload)
# if resp.status_code in (200, 201):
#     user_created = resp.json()
#     print(f"✅ Motorista sincronizado: {json.dumps(user_created, indent=2)}")
#     if user_created.get("id") != driver_data["id"]:
#         print("❌ ID retornado diferente do enviado. Abortando.")
#         exit(1)
# else:
#     print(f"⚠️ Erro ao sincronizar: {resp.status_code} - {resp.text[:200]}")
#     resp_get = requests.get(f"{RIDE_SERVICE_URL}/api/ride/users/{driver_data['id']}/")
#     if resp_get.status_code == 200:
#         print("✅ Motorista já existente no ride-service.")
#     else:
#         print("❌ Motorista não encontrado. Abortando.")
#         exit(1)

# # ------------------------------------------------------------
# # 3. Profile e refresh
# # ------------------------------------------------------------
# print("\n✏️ Atualizando perfil (PATCH /api/profile/)...")
# resp = req("PATCH", f"{BASE_URL}/api/profile/", data={"telefone": "11999999999"}, headers=auth_header(driver_access))
# check_response(resp, 200)

# print("\n🔄 Refresh token (POST /api/token/refresh/)...")
# resp = req("POST", f"{BASE_URL}/api/token/refresh/", data={"refresh": driver_refresh})
# tokens = check_response(resp, 200)
# new_driver_access = tokens["access"]
# new_driver_refresh = tokens.get("refresh", driver_refresh)
# print("✅ Token refresh OK")

# # ------------------------------------------------------------
# # 4. Criar veículos
# # ------------------------------------------------------------
# print("\n🚗 Criando veículo 1...")
# vehicle_data = {
#     "user": driver_data["id"], "model": "Fiat Uno", "color": "vermelho",
#     "plate": "ABC1D23", "seats": 5, "type_vehicle": "carro"
# }
# resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", data=vehicle_data, headers=auth_header(new_driver_access))
# vehicle1 = check_response(resp, 201)
# vehicle1_id = vehicle1["id"]
# print(f"✅ Veículo 1 criado:\n{json.dumps(vehicle1, indent=2)}")

# print("\n🚗 Criando veículo 2...")
# vehicle2_data = {
#     "user": driver_data["id"], "model": "Ford Ka", "color": "azul",
#     "plate": "XYZ9A87", "seats": 4, "type_vehicle": "carro"
# }
# resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", data=vehicle2_data, headers=auth_header(new_driver_access))
# vehicle2 = check_response(resp, 201)
# vehicle2_id = vehicle2["id"]
# print(f"✅ Veículo 2 criado:\n{json.dumps(vehicle2, indent=2)}")

# # ------------------------------------------------------------
# # 5. Testar endpoints de veículos
# # ------------------------------------------------------------
# print("\n📋 Listando veículos...")
# resp = req("GET", f"{BASE_URL}/api/ride/vehicles/", headers=auth_header(new_driver_access))
# veiculos = check_response(resp, 200)
# print(f"✅ Veículos: {len(veiculos)}\n{json.dumps(veiculos, indent=2)}")

# print(f"\n🔍 Detalhe veículo {vehicle1_id}...")
# resp = req("GET", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", headers=auth_header(new_driver_access))
# print(f"✅ Detalhe:\n{json.dumps(resp.json(), indent=2)}")

# print(f"\n✏️ Atualizar veículo {vehicle1_id}...")
# resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", data={"color": "azul"}, headers=auth_header(new_driver_access))
# print(f"✅ Atualizado:\n{json.dumps(resp.json(), indent=2)}")

# print(f"\n🗑️ Deletar veículo {vehicle2_id}...")
# resp = req("DELETE", f"{BASE_URL}/api/ride/vehicles/{vehicle2_id}/", headers=auth_header(new_driver_access))
# if resp.status_code == 204:
#     print("✅ Veículo 2 deletado")
# else:
#     print(f"⚠️ Status {resp.status_code}")

# # ------------------------------------------------------------
# # 6. Criar caronas
# # ------------------------------------------------------------
# print("\n🚕 Criando carona 1...")
# start_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
# expected_arrival = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
# ride_data = {
#     "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "Aeroporto",
#     "start_time": start_time, "expected_arrival": expected_arrival,
#     "available_seats": 3, "status": "pendente", "price": 45.00
# }
# resp = req("POST", f"{BASE_URL}/api/ride/rides/", data=ride_data, headers=auth_header(new_driver_access))
# ride1 = check_response(resp, 201)
# ride1_id = ride1["id"]
# ride1_uuid = ride1["id"]
# print(f"✅ Carona 1 criada:\n{json.dumps(ride1, indent=2)}")

# print("\n🚕 Criando carona 2...")
# ride2_data = {
#     "vehicle": vehicle1_id, "origin": "Centro", "destination": "Shopping",
#     "start_time": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
#     "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
#     "available_seats": 2, "status": "pendente", "price": 20.00
# }
# resp = req("POST", f"{BASE_URL}/api/ride/rides/", data=ride2_data, headers=auth_header(new_driver_access))
# ride2 = check_response(resp, 201)
# ride2_id = ride2["id"]
# print(f"✅ Carona 2 criada:\n{json.dumps(ride2, indent=2)}")

# # ------------------------------------------------------------
# # 7. Testar endpoints de rides
# # ------------------------------------------------------------
# print("\n📋 Listando caronas...")
# resp = req("GET", f"{BASE_URL}/api/ride/rides/", headers=auth_header(new_driver_access))
# caronas = check_response(resp, 200)
# print(f"✅ Caronas: {len(caronas)}\n{json.dumps(caronas, indent=2)}")

# print(f"\n🔍 Detalhe carona {ride1_id}...")
# resp = req("GET", f"{BASE_URL}/api/ride/rides/{ride1_id}/", headers=auth_header(new_driver_access))
# print(f"✅ Detalhe:\n{json.dumps(resp.json(), indent=2)}")

# print(f"\n✏️ Atualizar carona {ride1_id}...")
# patch_ride = {
#     "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "centro",
#     "start_time": start_time, "expected_arrival": expected_arrival,
#     "available_seats": 3, "status": "pendente", "price": "45.00"
# }
# resp = req("PATCH", f"{BASE_URL}/api/ride/rides/{ride1_id}/", data=patch_ride, headers=auth_header(new_driver_access))
# print(f"✅ Atualizada:\n{json.dumps(resp.json(), indent=2)}")

# # ------------------------------------------------------------
# # 8. Reservas
# # ------------------------------------------------------------

# # Sincronização manual do passageiro no ride-service (porta 8004)
# print("\n👤 Sincronizando passageiro no ride-service...")
# user_payload = {
#     "id": passenger_data["id"],
#     "name": passenger_data["nome"],
#     "is_driver": False
# }
# resp = requests.post(f"{RIDE_SERVICE_URL}/api/ride/users/", json=user_payload)
# if resp.status_code in (200, 201):
#     print("✅ Passageiro sincronizado com sucesso!")
# else:
#     print(f"⚠️ Erro ao sincronizar: {resp.status_code} - {resp.text[:200]}")
#     resp_get = requests.get(f"{RIDE_SERVICE_URL}/api/ride/users/{passenger_data['id']}/")
#     if resp_get.status_code == 200:
#         print("✅ Passageiro já existente no ride-service.")
#     else:
#         print("❌ Passageiro não encontrado. Abortando.")
#         exit(1)

# print("\n📅 Criando reserva...")
# reservation_data = {
#     "ride": ride1_id, "passenger": passenger_data["id"],
#     "requested_seats": 2, "status": "pendente"
# }
# resp = req("POST", f"{BASE_URL}/api/ride/reservations/", data=reservation_data, headers=auth_header(passenger_access))
# reservation1 = check_response(resp, 201)
# reservation1_id = reservation1["id"]
# print(f"✅ Reserva criada:\n{json.dumps(reservation1, indent=2)}")

# print("\n📋 Listando reservas...")
# resp = req("GET", f"{BASE_URL}/api/ride/reservations/", headers=auth_header(passenger_access))
# reservas = check_response(resp, 200)
# print(f"✅ Reservas: {len(reservas)}\n{json.dumps(reservas, indent=2)}")

# print(f"\n🔍 Detalhe reserva {reservation1_id}...")
# resp = req("GET", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", headers=auth_header(passenger_access))
# print(f"✅ Detalhe:\n{json.dumps(resp.json(), indent=2)}")

# print(f"\n✏️ Confirmar reserva {reservation1_id}...")
# resp = req("PATCH", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", data={"status": "confirmada"}, headers=auth_header(passenger_access))
# print(f"✅ Confirmada:\n{json.dumps(resp.json(), indent=2)}")

# # Notificações após reserva
# print("\n⏳ Aguardando notificações (5s)...")
# time.sleep(5)

# print("\n🔔 Notificações do motorista (após reserva):")
# resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
# print(f"✅ {json.dumps(resp.json(), indent=2)}")

# print("\n🔔 Notificações do passageiro (após reserva):")
# resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
# print(f"✅ {json.dumps(resp.json(), indent=2)}")

# # ------------------------------------------------------------
# # 9. Chat
# # ------------------------------------------------------------
# print("\n💬 Chat: obtendo ou criando sala...")
# time.sleep(3)

# resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/", headers=auth_header(passenger_access))
# if resp_get.status_code == 200:
#     room = resp_get.json()
#     print(f"✅ Sala já existente:\n{json.dumps(room, indent=2)}")
# else:
#     chat_payload = {
#         "carona_id": ride1_uuid,
#         "driver_id": driver_data["id"],
#         "passenger_ids": [passenger_data["id"]]
#     }
#     resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", data=chat_payload, headers=auth_header(passenger_access))
#     if resp_post.status_code in (200, 201):
#         room = resp_post.json()
#         print(f"✅ Sala criada:\n{json.dumps(room, indent=2)}")
#     else:
#         print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
#         room = None

# if room:
#     msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
#     print("\n💬 Enviando mensagem do passageiro...")
#     resp = req("POST", msg_url, data={"usuario_id": passenger_data["id"], "conteudo": "Olá, motorista! Estou no ponto."}, headers=auth_header(passenger_access))
#     msg_pass = check_response(resp, 201)
#     print(f"✅ Mensagem enviada:\n{json.dumps(msg_pass, indent=2)}")

#     print("\n💬 Enviando mensagem do motorista...")
#     resp = req("POST", msg_url, data={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
#     msg_motorista = check_response(resp, 201)
#     print(f"✅ Mensagem enviada:\n{json.dumps(msg_motorista, indent=2)}")

#     print("\n📜 Histórico de mensagens...")
#     resp = req("GET", msg_url, headers=auth_header(passenger_access))
#     messages = check_response(resp, 200)
#     print(f"✅ {len(messages)} mensagens:\n{json.dumps(messages, indent=2)}")

#     # Notificações pós-chat
#     print("\n⏳ Aguardando notificações do chat (5s)...")
#     time.sleep(5)

#     print("\n🔔 Notificações do motorista (após chat):")
#     resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
#     print(f"✅ {json.dumps(resp.json(), indent=2)}")

#     print("\n🔔 Notificações do passageiro (após chat):")
#     resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
#     print(f"✅ {json.dumps(resp.json(), indent=2)}")
# else:
#     print("⚠️ Chat não disponível.")

# # ------------------------------------------------------------
# # 10. Logout
# # ------------------------------------------------------------
# print("\n🚪 Logout...")
# logout_refresh = new_driver_refresh if new_driver_refresh else driver_refresh
# resp = req("POST", f"{BASE_URL}/api/logout/", data={"refresh": logout_refresh}, headers=auth_header(new_driver_access))
# if resp.status_code == 205:
#     print("✅ Logout realizado")
# else:
#     print(f"⚠️ Status {resp.status_code}")

# print("\n🎉 Testes concluídos com sucesso!")


import requests
import uuid
import random
import time
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000"

# ------------------------------------------------------------
# Utilitários
# ------------------------------------------------------------
def gerar_cpf():
    def digito(digs):
        s = sum(d * (len(digs)+1 - i) for i, d in enumerate(digs))
        d = 11 - (s % 11)
        return d if d < 10 else 0
    base = [random.randint(0, 9) for _ in range(9)]
    base.append(digito(base))
    base.append(digito(base))
    cpf_str = ''.join(map(str, base))
    return f'{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}'

def random_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

def check_response(resp, success_code=200):
    if resp.status_code != success_code:
        print(f"❌ Erro {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()
    return resp.json()

def get_tokens(email, password):
    resp = requests.post(f"{BASE_URL}/api/login/", data={"email": email, "password": password})
    data = check_response(resp)
    return data["access"], data["refresh"]

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}

# Função de requisição com log detalhado e formatação
def req(method, url, **kwargs):
    headers = kwargs.get("headers")
    # Mascarar token no log se presente
    masked_headers = None
    if headers and "Authorization" in headers:
        token = headers["Authorization"].split()[1]
        masked = token[:10] + "..." + token[-10:] if len(token) > 20 else token
        masked_headers = {"Authorization": f"Bearer {masked}"}
    else:
        masked_headers = headers

    # Prepara o corpo para exibição formatada
    body = None
    if "data" in kwargs:
        body = kwargs["data"]
    elif "json" in kwargs:
        body = kwargs["json"]

    print(f"\n➡️ {method} {url}")
    if masked_headers:
        print(f"   headers: {json.dumps(masked_headers, indent=2)}")
    if body:
        print(f"   body:\n{json.dumps(body, indent=2, ensure_ascii=False)}")
    
    resp = requests.request(method, url, **kwargs)
    print(f"⬅️ {resp.status_code}")
    return resp

# ------------------------------------------------------------
# 1. Registrar usuários
# ------------------------------------------------------------
driver_email = random_email()
passenger_email = random_email()
password = "Teste@123"

print("\n📝 Registrando motorista...")
resp = req("POST", f"{BASE_URL}/api/register/", data={
    "email": driver_email, "nome": "Motorista Silva", "password": password,
    "cpf": gerar_cpf(), "telefone": "11999990001", "tipo_usuario": "Motorista",
})
driver_data = check_response(resp, 201)
print(f"✅ Motorista registrado:\n{json.dumps(driver_data, indent=2)}")

print("\n📝 Registrando passageiro...")
resp = req("POST", f"{BASE_URL}/api/register/", data={
    "email": passenger_email, "nome": "Passageiro Santos", "password": password,
    "cpf": gerar_cpf(), "telefone": "11999990002", "tipo_usuario": "Passageiro",
})
passenger_data = check_response(resp, 201)
print(f"✅ Passageiro registrado:\n{json.dumps(passenger_data, indent=2)}")

print("\n⏳ Aguardando sincronização Kafka (5s)...")
time.sleep(9)

# ------------------------------------------------------------
# 2. Login
# ------------------------------------------------------------
print("\n🔐 Fazendo login...")
driver_access, driver_refresh = get_tokens(driver_email, password)
passenger_access, passenger_refresh = get_tokens(passenger_email, password)
print("✅ Tokens obtidos")

# ------------------------------------------------------------
# 3. Profile e refresh
# ------------------------------------------------------------
print("\n✏️ Atualizando perfil (PATCH /api/profile/)...")
resp = req("PATCH", f"{BASE_URL}/api/profile/", data={"telefone": "11999999999"}, headers=auth_header(driver_access))
check_response(resp, 200)

print("\n🔄 Refresh token (POST /api/token/refresh/)...")
resp = req("POST", f"{BASE_URL}/api/token/refresh/", data={"refresh": driver_refresh})
tokens = check_response(resp, 200)
new_driver_access = tokens["access"]
new_driver_refresh = tokens.get("refresh", driver_refresh)
print("✅ Token refresh OK")

# ------------------------------------------------------------
# 4. Criar veículos
# ------------------------------------------------------------
print("\n🚗 Criando veículo 1...")
vehicle_data = {
    "user": driver_data["id"], "model": "Fiat Uno", "color": "vermelho",
    "plate": "ABC1D23", "seats": 5,
    "type_vehicle": "carro" 
}
resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", data=vehicle_data, headers=auth_header(new_driver_access))
vehicle1 = check_response(resp, 201)
vehicle1_id = vehicle1["id"]
print(f"✅ Veículo 1 criado:\n{json.dumps(vehicle1, indent=2)}")

print("\n🚗 Criando veículo 2...")
vehicle2_data = {
    "user": driver_data["id"], "model": "Ford Ka", "color": "azul",
    "plate": "XYZ9A87", "seats": 4,
    "type_vehicle": "carro" 
}
resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", data=vehicle2_data, headers=auth_header(new_driver_access))
vehicle2 = check_response(resp, 201)
vehicle2_id = vehicle2["id"]
print(f"✅ Veículo 2 criado:\n{json.dumps(vehicle2, indent=2)}")

# ------------------------------------------------------------
# 5. Testar endpoints de veículos
# ------------------------------------------------------------
print("\n📋 Listando veículos (GET)...")
resp = req("GET", f"{BASE_URL}/api/ride/vehicles/", headers=auth_header(new_driver_access))
veiculos = check_response(resp, 200)
print(f"✅ Veículos encontrados: {len(veiculos)}\n{json.dumps(veiculos, indent=2)}")

print(f"\n🔍 Detalhe veículo {vehicle1_id} (GET)...")
resp = req("GET", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", headers=auth_header(new_driver_access))
veiculo_detalhe = check_response(resp, 200)
print(f"✅ Detalhe:\n{json.dumps(veiculo_detalhe, indent=2)}")

print(f"\n✏️ Atualizar veículo {vehicle1_id} (PATCH)...")
# resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", data={"color": "Vermelho"}, headers=auth_header(new_driver_access))
resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", data={"color": "azul"}, headers=auth_header(new_driver_access))
veiculo_atualizado = check_response(resp, 200)
print(f"✅ Veículo atualizado:\n{json.dumps(veiculo_atualizado, indent=2)}")

print(f"\n🗑️ Deletar veículo {vehicle2_id} (DELETE)...")
resp = req("DELETE", f"{BASE_URL}/api/ride/vehicles/{vehicle2_id}/", headers=auth_header(new_driver_access))
if resp.status_code == 204:
    print("✅ Veículo 2 deletado")
else:
    print(f"⚠️ DELETE retornou {resp.status_code}")

# ------------------------------------------------------------
# 6. Criar caronas
# ------------------------------------------------------------
print("\n🚕 Criando carona 1...")
start_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
expected_arrival = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
ride_data = {
    "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "Aeroporto",
    "start_time": start_time, "expected_arrival": expected_arrival,
    "available_seats": 3, "status": "pendente", "price": 45.00
}
resp = req("POST", f"{BASE_URL}/api/ride/rides/", data=ride_data, headers=auth_header(new_driver_access))
ride1 = check_response(resp, 201)
ride1_id = ride1["id"]
ride1_uuid = ride1["id"]   # id é o UUID da carona
print(f"✅ Carona 1 criada:\n{json.dumps(ride1, indent=2)}")

print("\n🚕 Criando carona 2...")
ride2_data = {
    "vehicle": vehicle1_id, "origin": "Centro", "destination": "Shopping",
    "start_time": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
    "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    "available_seats": 2, "status": "pendente", "price": 20.00
}
resp = req("POST", f"{BASE_URL}/api/ride/rides/", data=ride2_data, headers=auth_header(new_driver_access))
ride2 = check_response(resp, 201)
ride2_id = ride2["id"]
print(f"✅ Carona 2 criada:\n{json.dumps(ride2, indent=2)}")

# ------------------------------------------------------------
# 7. Testar endpoints de rides
# ------------------------------------------------------------
print("\n📋 Listando caronas (GET)...")
resp = req("GET", f"{BASE_URL}/api/ride/rides/", headers=auth_header(new_driver_access))
caronas = check_response(resp, 200)
print(f"✅ Caronas encontradas: {len(caronas)}\n{json.dumps(caronas, indent=2)}")

print(f"\n🔍 Detalhe carona {ride1_id} (GET)...")
resp = req("GET", f"{BASE_URL}/api/ride/rides/{ride1_id}/", headers=auth_header(new_driver_access))
carona_detalhe = check_response(resp, 200)
print(f"✅ Detalhe:\n{json.dumps(carona_detalhe, indent=2)}")

print(f"\n✏️ Atualizar carona {ride1_id} (PATCH)...")
patch_ride = {
    "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "centro",
    "start_time": start_time, "expected_arrival": expected_arrival,
    "available_seats": 3, "status": "pendente", "price": "45.00"
}
resp = req("PATCH", f"{BASE_URL}/api/ride/rides/{ride1_id}/", data=patch_ride, headers=auth_header(new_driver_access))
carona_atualizada = check_response(resp, 200)
print(f"✅ Carona atualizada:\n{json.dumps(carona_atualizada, indent=2)}")

# ------------------------------------------------------------
# 8. Reservas
# ------------------------------------------------------------

# ------------------------------------------------------------
# Sincronização manual do passageiro no ride-service
# ------------------------------------------------------------
print("\n👤 Sincronizando passageiro no serviço de caronas...")
user_payload = {
    "id": passenger_data["id"],          # mesmo UUID do registro
    "name": passenger_data["nome"],
    "is_driver": False
}
resp = req("POST", f"{BASE_URL}/api/ride/users/", data=user_payload, headers=auth_header(passenger_access))

if resp.status_code in (200, 201):
    print("✅ Passageiro sincronizado com sucesso!")
else:
    print(f"⚠️ Erro ao sincronizar: {resp.status_code} - {resp.text[:200]}")
    # Verifica se já existe (caso o Kafka tenha funcionado)
    resp_get = req("GET", f"{BASE_URL}/api/ride/users/{passenger_data['id']}/", headers=auth_header(passenger_access))
    if resp_get.status_code == 200:
        print("✅ Passageiro já existe no ride-service (ignorando erro).")
    else:
        print("❌ Passageiro não encontrado e não foi possível criá-lo. Abortando reserva.")
        exit(1)


print("\n📅 Criando reserva...")
reservation_data = {
    "ride": ride1_id, "passenger": passenger_data["id"],
    "requested_seats": 2, "status": "pendente"
}
resp = req("POST", f"{BASE_URL}/api/ride/reservations/", data=reservation_data, headers=auth_header(passenger_access))
reservation1 = check_response(resp, 201)
reservation1_id = reservation1["id"]
print(f"✅ Reserva criada:\n{json.dumps(reservation1, indent=2)}")

print("\n📋 Listando reservas (GET)...")
resp = req("GET", f"{BASE_URL}/api/ride/reservations/", headers=auth_header(passenger_access))
reservas = check_response(resp, 200)
print(f"✅ Reservas encontradas: {len(reservas)}\n{json.dumps(reservas, indent=2)}")

print(f"\n🔍 Detalhe reserva {reservation1_id} (GET)...")
resp = req("GET", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", headers=auth_header(passenger_access))
reserva_detalhe = check_response(resp, 200)
print(f"✅ Detalhe:\n{json.dumps(reserva_detalhe, indent=2)}")

print(f"\n✏️ Confirmar reserva {reservation1_id} (PATCH)...")
resp = req("PATCH", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", data={"status": "confirmada"}, headers=auth_header(passenger_access))
reserva_confirmada = check_response(resp, 200)
print(f"✅ Reserva confirmada:\n{json.dumps(reserva_confirmada, indent=2)}")

# ============================================================
# NOVIDADE: VERIFICAÇÃO DE NOTIFICAÇÕES APÓS RESERVA
# ============================================================
print("\n⏳ Aguardando processamento das notificações (5s)...")
time.sleep(5)

print("\n🔔 Notificações do motorista (após reserva):")
resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
notif_driver = check_response(resp, 200)
print(f"✅ Notificações motorista:\n{json.dumps(notif_driver, indent=2)}")

print("\n🔔 Notificações do passageiro (após reserva):")
resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
notif_passenger = check_response(resp, 200)
print(f"✅ Notificações passageiro:\n{json.dumps(notif_passenger, indent=2)}")
# ------------------------------------------------------------
# 9. Chat - criação com motorista e passageiros
# ------------------------------------------------------------
print("\n💬 Chat: obtendo ou criando sala com participantes...")
time.sleep(3)

# Tenta obter a sala primeiro
resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/", headers=auth_header(passenger_access))
if resp_get.status_code == 200:
    room = resp_get.json()
    print(f"✅ Sala já existente: {json.dumps(room, indent=2)}")
    # Se a sala já existe, mas foi criada sem participantes, você pode optar por deletá-la e recriar.
    # Como o endpoint DELETE não está disponível, vamos apenas alertar e pular.
    # Para garantir, você pode implementar um DELETE manualmente ou usar um PATCH para adicionar os participantes (se houver).
    # A melhor abordagem é sempre criar com participantes na primeira vez.
else:
    # Sala não existe: criar com motorista e passageiros
    chat_payload = {
        "carona_id": ride1_uuid,
        "driver_id": driver_data["id"],
        "passenger_ids": [passenger_data["id"]]
    }
    resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", data=chat_payload, headers=auth_header(passenger_access))
    if resp_post.status_code in (200, 201):
        room = resp_post.json()
        print(f"✅ Sala criada com participantes:\n{json.dumps(room, indent=2)}")
    else:
        print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
        room = None

if room:
    msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
    print("\n💬 Enviando mensagem do passageiro...")
    resp = req("POST", msg_url, data={"usuario_id": passenger_data["id"], "conteudo": "Olá, motorista! Estou no ponto."}, headers=auth_header(passenger_access))
    msg_pass = check_response(resp, 201)
    print(f"✅ Mensagem enviada:\n{json.dumps(msg_pass, indent=2)}")

    print("\n💬 Enviando mensagem do motorista...")
    resp = req("POST", msg_url, data={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
    msg_motorista = check_response(resp, 201)
    print(f"✅ Mensagem enviada:\n{json.dumps(msg_motorista, indent=2)}")

    print("\n📜 Obtendo histórico de mensagens...")
    resp = req("GET", msg_url, headers=auth_header(passenger_access))
    messages = check_response(resp, 200)
    print(f"✅ {len(messages)} mensagens trocadas:\n{json.dumps(messages, indent=2)}")
else:
    print("⚠️ Pulando chat devido a erro na criação/obtenção da sala")

# Aguarda processamento das notificações de chat
print("\n⏳ Aguardando processamento das notificações de chat (5s)...")
time.sleep(5)

print("\n🔔 Notificações do motorista (após chat):")
resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
notif_driver2 = check_response(resp, 200)
print(f"✅ Notificações motorista:\n{json.dumps(notif_driver2, indent=2)}")

print("\n🔔 Notificações do passageiro (após chat):")
resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
notif_passenger2 = check_response(resp, 200)
print(f"✅ Notificações passageiro:\n{json.dumps(notif_passenger2, indent=2)}")

# ============================================================
# NOVIDADE: VERIFICAÇÃO DE NOTIFICAÇÕES APÓS CHAT
# ============================================================
print("\n⏳ Aguardando processamento das notificações de chat (5s)...")
time.sleep(5)

print("\n🔔 Notificações do motorista (após chat):")
resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
notif_driver2 = check_response(resp, 200)
print(f"✅ Notificações motorista:\n{json.dumps(notif_driver2, indent=2)}")

print("\n🔔 Notificações do passageiro (após chat):")
resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
notif_passenger2 = check_response(resp, 200)
print(f"✅ Notificações passageiro:\n{json.dumps(notif_passenger2, indent=2)}")
# ------------------------------------------------------------
# 10. Chat e notificações de chat (CORRIGIDO)
# ------------------------------------------------------------
print("\n" + "="*60)
print("10. CHAT E NOTIFICAÇÕES DE CHAT")
print("="*60)

print("\n💬 Verificando se a sala de chat foi criada automaticamente (via Kafka) após confirmação da carona...")
time.sleep(5)
resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/", headers=auth_header(passenger_access))
if resp_get.status_code == 200:
    room = resp_get.json()
    print(f"✅ Sala encontrada (criada automaticamente):\n{json.dumps(room, indent=2)}")
else:
    print("⚠️ Sala não encontrada. Criando manualmente com motorista e passageiros...")
    chat_payload = {
        "carona_id": ride1_uuid,
        "driver_id": driver_data["id"],
        "passenger_ids": [passenger_data["id"]]
    }
    resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", data=chat_payload, headers=auth_header(passenger_access))
    if resp_post.status_code in (200, 201):
        room = resp_post.json()
        print(f"✅ Sala criada com participantes:\n{json.dumps(room, indent=2)}")
    else:
        print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
        room = None

if room:
    msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
    print("\n💬 Enviando mensagem do motorista...")
    resp = req("POST", msg_url, data={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
    msg_motorista = check_response(resp, 201)
    if msg_motorista is not None:
        print(f"✅ Mensagem do motorista enviada:\n{json.dumps(msg_motorista, indent=2)}")
    else:
        print("⚠️ Falha ao enviar mensagem do motorista")

    print("\n💬 Enviando mensagem do passageiro...")
    resp = req("POST", msg_url, data={"usuario_id": passenger_data["id"], "conteudo": "Olá, estou no ponto!"}, headers=auth_header(passenger_access))
    msg_passageiro = check_response(resp, 201)
    if msg_passageiro is not None:
        print(f"✅ Mensagem do passageiro enviada:\n{json.dumps(msg_passageiro, indent=2)}")
    else:
        print("⚠️ Falha ao enviar mensagem do passageiro")

    print("\n📜 Obtendo histórico de mensagens...")
    resp = req("GET", msg_url, headers=auth_header(passenger_access))
    messages = check_response(resp, 200)
    if messages is not None:
        print(f"✅ {len(messages)} mensagens trocadas:\n{json.dumps(messages, indent=2)}")
    else:
        print("⚠️ Falha ao obter mensagens")

    print("\n⏳ Aguardando processamento das notificações do chat (5s)...")
    time.sleep(5)

    print("\n--- Notificações do motorista (agora com chat) ---")
    resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
    notificacoes_motorista_chat = check_response(resp, 200)
    if notificacoes_motorista_chat is not None:
        print(json.dumps(notificacoes_motorista_chat, indent=2))
    else:
        print("⚠️ Falha ao obter notificações do motorista")

    print("\n--- Notificações do passageiro (agora com chat) ---")
    resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
    notificacoes_passageiro_chat = check_response(resp, 200)
    if notificacoes_passageiro_chat is not None:
        print(json.dumps(notificacoes_passageiro_chat, indent=2))
    else:
        print("⚠️ Falha ao obter notificações do passageiro")
else:
    print("⚠️ Pulando chat devido a erro na criação/obtenção da sala")

# ------------------------------------------------------------
# 11. Logout
# ------------------------------------------------------------
print("\n🚪 Logout (POST /api/logout/)...")
logout_refresh = new_driver_refresh if new_driver_refresh else driver_refresh
resp = req("POST", f"{BASE_URL}/api/logout/", data={"refresh": logout_refresh}, headers=auth_header(new_driver_access))
if resp.status_code == 205:
    print("✅ Logout realizado")
else:
    print(f"⚠️ Logout retornou {resp.status_code}")

print("\n🎉 Testes concluídos com logs detalhados e formatados!")



import requests
import uuid
import time
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8004"

# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------
def check_response(resp, success_code=200):
    if resp.status_code != success_code:
        print(f"❌ Erro {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()

def req(method, url, **kwargs):
    headers = kwargs.get("headers", {})
    body = None
    if "data" in kwargs:
        body = kwargs["data"]
    elif "json" in kwargs:
        body = kwargs["json"]

    print(f"\n➡️ {method} {url}")
    if headers:
        print(f"   headers: {json.dumps(headers, indent=2)}")
    if body:
        print(f"   body:\n{json.dumps(body, indent=2, ensure_ascii=False)}")

    resp = requests.request(method, url, **kwargs)
    print(f"⬅️ {resp.status_code}")
    return resp

# ------------------------------------------------------------
# 1. Criar usuários
# ------------------------------------------------------------
print("\n📝 Criando motorista 1 (is_driver=True)...")
driver1_payload = {
    "id": str(uuid.uuid4()),
    "name": "Motorista IA 1",
    "is_driver": True
}
resp = req("POST", f"{BASE_URL}/api/ride/users/", data=driver1_payload)
driver1 = check_response(resp, 201)
print(f"✅ Motorista 1 criado: {json.dumps(driver1, indent=2)}")

print("\n📝 Criando motorista 2 (is_driver=True)...")
driver2_payload = {
    "id": str(uuid.uuid4()),
    "name": "Motorista IA 2",
    "is_driver": True
}
resp = req("POST", f"{BASE_URL}/api/ride/users/", data=driver2_payload)
driver2 = check_response(resp, 201)
print(f"✅ Motorista 2 criado: {json.dumps(driver2, indent=2)}")

print("\n📝 Criando passageiro (is_driver=False)...")
passenger_payload = {
    "id": str(uuid.uuid4()),
    "name": "Passageiro IA",
    "is_driver": False
}
resp = req("POST", f"{BASE_URL}/api/ride/users/", data=passenger_payload)
passenger = check_response(resp, 201)
print(f"✅ Passageiro criado: {json.dumps(passenger, indent=2)}")

# ------------------------------------------------------------
# 2. Criar veículos
# ------------------------------------------------------------
print("\n🚗 Criando veículo para motorista 1...")
vehicle1_payload = {
    "user": driver1["id"],
    "model": "HB20",
    "type_vehicle": "carro",
    "color": "preto",
    "plate": "TES-1234",
    "seats": 5
}
resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", data=vehicle1_payload)
vehicle1 = check_response(resp, 201)
vehicle1_id = vehicle1["id"]
print(f"✅ Veículo 1 criado: {json.dumps(vehicle1, indent=2)}")

print("\n🚗 Criando veículo para motorista 2...")
vehicle2_payload = {
    "user": driver2["id"],
    "model": "Ford Ka",
    "type_vehicle": "carro",
    "color": "azul",
    "plate": "XYZ-9876",
    "seats": 4
}
resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", data=vehicle2_payload)
vehicle2 = check_response(resp, 201)
vehicle2_id = vehicle2["id"]
print(f"✅ Veículo 2 criado: {json.dumps(vehicle2, indent=2)}")

# ------------------------------------------------------------
# 3. Criar caronas (3 do motorista 1, 2 do motorista 2)
# ------------------------------------------------------------
rides = []
origins = ["Terminal Central", "Shopping", "Aeroporto", "Centro", "Rodoviária"]
destinations = ["Shopping", "Terminal Central", "Centro", "Aeroporto", "Rodoviária"]
prices = [25.00, 30.00, 45.00, 20.00, 35.00]

# Primeiras 3 caronas com motorista 1
for i in range(3):
    start = (datetime.now(timezone.utc) + timedelta(hours=i+1)).isoformat()
    arrival = (datetime.now(timezone.utc) + timedelta(hours=i+2)).isoformat()
    ride_data = {
        "vehicle": vehicle1_id,
        "origin": origins[i],
        "destination": destinations[i],
        "start_time": start,
        "expected_arrival": arrival,
        "available_seats": 3,
        "status": "pendente",
        "price": prices[i]
    }
    resp = req("POST", f"{BASE_URL}/api/ride/rides/", data=ride_data)
    ride = check_response(resp, 201)
    rides.append(ride)
    print(f"✅ Carona {i+1} criada (motorista 1): id={ride['id']}")

# Próximas 2 caronas com motorista 2
for i in range(3, 5):
    start = (datetime.now(timezone.utc) + timedelta(hours=i+1)).isoformat()
    arrival = (datetime.now(timezone.utc) + timedelta(hours=i+2)).isoformat()
    ride_data = {
        "vehicle": vehicle2_id,
        "origin": origins[i],
        "destination": destinations[i],
        "start_time": start,
        "expected_arrival": arrival,
        "available_seats": 2,   # veículo 2 tem apenas 4 assentos
        "status": "pendente",
        "price": prices[i]
    }
    resp = req("POST", f"{BASE_URL}/api/ride/rides/", data=ride_data)
    ride = check_response(resp, 201)
    rides.append(ride)
    print(f"✅ Carona {i+1} criada (motorista 2): id={ride['id']}")

# ------------------------------------------------------------
# 4. Criar reservas para gerar histórico (3 primeiras caronas)
# ------------------------------------------------------------
print("\n📅 Criando reservas (histórico)...")
for idx, ride in enumerate(rides[:3]):
    reservation_payload = {
        "ride": ride["id"],
        "passenger": passenger["id"],
        "requested_seats": 1,
        "status": "confirmada"
    }
    resp = req("POST", f"{BASE_URL}/api/ride/reservations/", data=reservation_payload)
    reservation = check_response(resp, 201)
    print(f"✅ Reserva {idx+1} criada e confirmada: id={reservation['id']}")

# Aguardar processamento (triggers assíncronos, se houver)
time.sleep(2)

# ------------------------------------------------------------
# 5. TESTAR RECOMENDAÇÃO COM IA (OLLAMA)
# ------------------------------------------------------------
print("\n🤖 Testando recomendação por IA...")
resp = req("GET", f"{BASE_URL}/api/ride/rides/ai-recommendations/?user_id={passenger['id']}&top_n=3")

if resp.status_code == 200:
    recommendations = resp.json()
    print(f"✅ Recomendações obtidas ({len(recommendations)} caronas):")
    for i, rec in enumerate(recommendations):
        print(f"\n--- Recomendação {i+1} ---")
        print(f"  Origem: {rec.get('origin')} → Destino: {rec.get('destination')}")
        print(f"  Preço: R$ {rec.get('price')}")
        print(f"  Partida: {rec.get('start_time')}")
        print(f"  Vagas: {rec.get('available_seats')}")
        print(f"  Status: {rec.get('status')}")
        print(f"  Motivo IA: {rec.get('ai_reason', '(não informado)')}")
else:
    print(f"❌ Falha na recomendação: {resp.status_code} - {resp.text}")

print("\n🎉 Teste finalizado!")


# ------------------------------------------------------------
# 6. TESTAR FILTRO COM IA (OLLAMA)
# ------------------------------------------------------------
print("\n" + "="*60)
print("🔍 Testando filtro inteligente com IA")
print("="*60)

# Texto de exemplo para filtrar caronas
texto_busca = "quero viajar do centro para o aeroporto amanhã, preço até 30 reais"

print(f"\n📝 Texto de busca: \"{texto_busca}\"")

resp = req("POST", f"{BASE_URL}/api/ride/rides/ai-filter/", data={"text": texto_busca})

if resp.status_code == 200:
    data = resp.json()
    print(f"✅ Filtro aplicado com sucesso!")
    print(f"\n📊 Filtros extraídos pela IA:")
    print(json.dumps(data.get('filters_applied', {}), indent=2, ensure_ascii=False))
    print(f"\n📋 Caronas encontradas: {data.get('count', 0)}")
    
    if data.get('results'):
        for i, ride in enumerate(data['results'], 1):
            print(f"\n--- Carona {i} ---")
            print(f"  ID: {ride.get('id')}")
            print(f"  Origem: {ride.get('origin')} → Destino: {ride.get('destination')}")
            print(f"  Partida: {ride.get('start_time')}")
            print(f"  Preço: R$ {ride.get('price')}")
            print(f"  Vagas: {ride.get('available_seats')}")
            print(f"  Status: {ride.get('status')}")
    else:
        print("  Nenhuma carona encontrada com os filtros extraídos.")
else:
    print(f"❌ Falha no filtro: {resp.status_code}")
    print(f"   Detalhes: {resp.text[:200]}")

# Teste com outro texto
print("\n" + "-"*40)
print("📝 Teste com outro texto: \"Shopping, carro, até 35 reais\"")
texto_busca2 ="Terminal Central para Shopping até 40"
resp = req("POST", f"{BASE_URL}/api/ride/rides/ai-filter/", data={"text": texto_busca2})

if resp.status_code == 200:
    data = resp.json()
    print(f"✅ Filtro aplicado com sucesso!")
    print(f"\n📊 Filtros extraídos pela IA:")
    print(json.dumps(data.get('filters_applied', {}), indent=2, ensure_ascii=False))
    print(f"\n📋 Caronas encontradas: {data.get('count', 0)}")
    
    if data.get('results'):
        for i, ride in enumerate(data['results'], 1):
            print(f"\n--- Carona {i} ---")
            print(f"  Origem: {ride.get('origin')} → Destino: {ride.get('destination')}")
            print(f"  Preço: R$ {ride.get('price')}")
    else:
        print("  Nenhuma carona encontrada.")
else:
    print(f"❌ Falha no filtro: {resp.status_code}")