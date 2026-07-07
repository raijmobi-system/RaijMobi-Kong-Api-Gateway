import requests
import uuid
import random
import time
import json
import jwt  # <-- novo
import os
from datetime import datetime, timedelta, timezone

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
RIDE_SERVICE_URL = os.getenv("RIDE_SERVICE_URL", "http://localhost:8002")
# Mesma SECRET_KEY usada no docker-compose.ci.yml para o ride-service
SECRET_KEY = "django-insecure-ride-ci-key"

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

def req(method, url, **kwargs):
    headers = kwargs.get("headers")
    masked_headers = None
    if headers and "Authorization" in headers:
        token = headers["Authorization"].split()[1]
        masked = token[:10] + "..." + token[-10:] if len(token) > 20 else token
        masked_headers = {"Authorization": f"Bearer {masked}"}
    else:
        masked_headers = headers

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

def get_admin_token():
    """Gera um token JWT para o admin criado no ride-service."""
    payload = {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "username": "ci_admin",
        "is_superuser": True
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

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
# 3. Sincronização manual com token de admin
# ------------------------------------------------------------
admin_token = get_admin_token()
admin_headers = {"Authorization": f"Bearer {admin_token}"}

print("\n👤 Sincronizando motorista no ride-service...")
driver_payload = {
    "id": driver_data["id"],
    "name": driver_data["nome"],
    "is_driver": True
}
resp = req("POST", f"{BASE_URL}/api/ride/users/", data=driver_payload, headers=admin_headers)
if resp.status_code in (200, 201):
    print("✅ Motorista sincronizado com sucesso!")
else:
    # Verifica se já existe
    resp_get = req("GET", f"{BASE_URL}/api/ride/users/{driver_data['id']}/", headers=admin_headers)
    if resp_get.status_code == 200:
        print("✅ Motorista já existente no ride-service.")
    else:
        print("❌ Falha crítica na sincronização do motorista. Abortando.")
        exit(1)

print("\n👤 Sincronizando passageiro no ride-service...")
passenger_payload = {
    "id": passenger_data["id"],
    "name": passenger_data["nome"],
    "is_driver": False
}
resp = req("POST", f"{BASE_URL}/api/ride/users/", data=passenger_payload, headers=admin_headers)
if resp.status_code in (200, 201):
    print("✅ Passageiro sincronizado com sucesso!")
else:
    resp_get = req("GET", f"{BASE_URL}/api/ride/users/{passenger_data['id']}/", headers=admin_headers)
    if resp_get.status_code == 200:
        print("✅ Passageiro já existente no ride-service.")
    else:
        print("❌ Passageiro não encontrado. Abortando.")
        exit(1)

# ------------------------------------------------------------
# 4. Profile e refresh (user-service)
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
# 5. Criar veículos
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
# 6. Testar endpoints de veículos
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
# 7. Criar caronas
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
# 8. Testar endpoints de rides
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
# 9. Reservas
# ------------------------------------------------------------
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
# Verificação de notificações após reserva
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
# 10. Chat
# ------------------------------------------------------------
print("\n💬 Chat: obtendo ou criando sala com participantes...")
time.sleep(3)

resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/", headers=auth_header(passenger_access))
if resp_get.status_code == 200:
    room = resp_get.json()
    print(f"✅ Sala já existente: {json.dumps(room, indent=2)}")
else:
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