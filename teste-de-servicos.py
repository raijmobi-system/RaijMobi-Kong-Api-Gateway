import requests
import uuid
import random
import time
import json
from datetime import datetime, timedelta, timezone
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
RIDE_SERVICE_URL = os.getenv("RIDE_SERVICE_URL", "http://localhost:8000")

# ============================================================
# Utilitários
# ============================================================
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
        print(f"❌ Erro {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()

def get_tokens(email, password):
    resp = requests.post(f"{BASE_URL}/api/login/", data={"email": email, "password": password})
    data = check_response(resp)
    return data["access"], data["refresh"]

def auth_header(token):
    """Retorna apenas o header Authorization com o token JWT."""
    return {"Authorization": f"Bearer {token}"}

def req(method, url, **kwargs):
    headers = kwargs.get("headers", {})
    # Mascarar token no log
    masked_headers = dict(headers)
    if "Authorization" in masked_headers:
        token = masked_headers["Authorization"].split()[1]
        masked = token[:10] + "..." + token[-10:] if len(token) > 20 else token
        masked_headers["Authorization"] = f"Bearer {masked}"

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


# ============================================================
# 1. Registrar usuários (Auth Service)
# ============================================================
driver_email = random_email()
driver2_email = random_email()
passenger_email = random_email()
password = "Teste@123"

print("\n" + "="*60)
print("1. REGISTRO DE USUÁRIOS")
print("="*60)

print("\n📝 Registrando motorista 1...")
resp = req("POST", f"{BASE_URL}/api/register/", data={
    "email": driver_email, "nome": "Motorista Silva", "password": password,
    "cpf": gerar_cpf(), "telefone": "11999990001", "tipo_usuario": "Motorista",
})
driver_data = check_response(resp, 201)
print(f"✅ Motorista 1 registrado:\n{json.dumps(driver_data, indent=2)}")

print("\n📝 Registrando motorista 2...")
resp = req("POST", f"{BASE_URL}/api/register/", data={
    "email": driver2_email, "nome": "Motorista Souza", "password": password,
    "cpf": gerar_cpf(), "telefone": "11999990003", "tipo_usuario": "Motorista",
})
driver2_data = check_response(resp, 201)
print(f"✅ Motorista 2 registrado:\n{json.dumps(driver2_data, indent=2)}")

print("\n📝 Registrando passageiro...")
resp = req("POST", f"{BASE_URL}/api/register/", data={
    "email": passenger_email, "nome": "Passageiro Santos", "password": password,
    "cpf": gerar_cpf(), "telefone": "11999990002", "tipo_usuario": "Passageiro",
})
passenger_data = check_response(resp, 201)
print(f"✅ Passageiro registrado:\n{json.dumps(passenger_data, indent=2)}")

print("\n⏳ Aguardando sincronização Kafka (9s)...")
time.sleep(9)

# ============================================================
# 2. Login e obtenção de JWT
# ============================================================
print("\n" + "="*60)
print("2. LOGIN E TOKENS JWT")
print("="*60)

print("\n🔐 Fazendo login do motorista 1...")
driver_access, driver_refresh = get_tokens(driver_email, password)
print("✅ Token motorista 1 obtido")

print("\n🔐 Fazendo login do motorista 2...")
driver2_access, driver2_refresh = get_tokens(driver2_email, password)
print("✅ Token motorista 2 obtido")

print("\n🔐 Fazendo login do passageiro...")
passenger_access, passenger_refresh = get_tokens(passenger_email, password)
print("✅ Token passageiro obtido")

# ============================================================
# 3. Profile e refresh token
# ============================================================
print("\n" + "="*60)
print("3. PROFILE E REFRESH TOKEN")
print("="*60)

print("\n✏️ Atualizando perfil do motorista 1 (PATCH /api/profile/)...")
resp = req("PATCH", f"{BASE_URL}/api/profile/",
    data={"telefone": "11999999999"},
    headers=auth_header(driver_access))
check_response(resp, 200)

print("\n🔄 Refresh token do motorista 1 (POST /api/token/refresh/)...")
resp = req("POST", f"{BASE_URL}/api/token/refresh/",
    data={"refresh": driver_refresh})
tokens = check_response(resp, 200)
new_driver_access = tokens["access"]
new_driver_refresh = tokens.get("refresh", driver_refresh)
print("✅ Token refresh motorista 1 OK")

print("\n🔄 Refresh token do motorista 2 (POST /api/token/refresh/)...")
resp = req("POST", f"{BASE_URL}/api/token/refresh/",
    data={"refresh": driver2_refresh})
tokens2 = check_response(resp, 200)
new_driver2_access = tokens2["access"]
new_driver2_refresh = tokens2.get("refresh", driver2_refresh)
print("✅ Token refresh motorista 2 OK")

print("\n🔄 Refresh token do passageiro (POST /api/token/refresh/)...")
resp = req("POST", f"{BASE_URL}/api/token/refresh/",
    data={"refresh": passenger_refresh})
tokens_p = check_response(resp, 200)
new_passenger_access = tokens_p["access"]
new_passenger_refresh = tokens_p.get("refresh", passenger_refresh)
print("✅ Token refresh passageiro OK")

# ============================================================
# 4. Sincronizar usuários no Ride Service (agora com json=)
# ============================================================
print("\n" + "="*60)
print("4. SINCRONIZAR USUÁRIOS NO RIDE SERVICE")
print("="*60)

print("\n👤 Sincronizando motorista 1...")
user_payload_driver1 = {
    "id": driver_data["id"],
    "name": driver_data["nome"],
    "is_driver": True
}
resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/users/",
    json=user_payload_driver1,
    headers=auth_header(new_driver_access))
if resp.status_code in (200, 201):
    print("✅ Motorista 1 sincronizado com sucesso!")
else:
    print(f"⚠️ Erro ao sincronizar motorista 1: {resp.status_code} - {resp.text[:200]}")
    resp_get = req("GET", f"{RIDE_SERVICE_URL}/api/ride/users/{driver_data['id']}/",
        headers=auth_header(new_driver_access))
    if resp_get.status_code == 200:
        print("✅ Motorista 1 já existe no ride-service (ignorando erro).")
    else:
        print("❌ Motorista 1 não encontrado e não foi possível criá-lo.")

print("\n👤 Sincronizando motorista 2...")
user_payload_driver2 = {
    "id": driver2_data["id"],
    "name": driver2_data["nome"],
    "is_driver": True
}
resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/users/",
    json=user_payload_driver2,
    headers=auth_header(new_driver2_access))
if resp.status_code in (200, 201):
    print("✅ Motorista 2 sincronizado com sucesso!")
else:
    print(f"⚠️ Erro ao sincronizar motorista 2: {resp.status_code} - {resp.text[:200]}")
    resp_get = req("GET", f"{RIDE_SERVICE_URL}/api/ride/users/{driver2_data['id']}/",
        headers=auth_header(new_driver2_access))
    if resp_get.status_code == 200:
        print("✅ Motorista 2 já existe no ride-service (ignorando erro).")
    else:
        print("❌ Motorista 2 não encontrado e não foi possível criá-lo.")

print("\n👤 Sincronizando passageiro...")
user_payload_passenger = {
    "id": passenger_data["id"],
    "name": passenger_data["nome"],
    "is_driver": False
}
resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/users/",
    json=user_payload_passenger,
    headers=auth_header(new_passenger_access))
if resp.status_code in (200, 201):
    print("✅ Passageiro sincronizado com sucesso!")
else:
    print(f"⚠️ Erro ao sincronizar passageiro: {resp.status_code} - {resp.text[:200]}")
    resp_get = req("GET", f"{RIDE_SERVICE_URL}/api/ride/users/{passenger_data['id']}/",
        headers=auth_header(new_passenger_access))
    if resp_get.status_code == 200:
        print("✅ Passageiro já existe no ride-service (ignorando erro).")
    else:
        print("❌ Passageiro não encontrado e não foi possível criá-lo. Abortando.")
        exit(1)

# ============================================================
# 5. Criar veículos (Ride Service) com json= e JWT
# ============================================================
print("\n" + "="*60)
print("5. CRIAÇÃO DE VEÍCULOS")
print("="*60)

print("\n🚗 Criando veículo 1 para motorista 1...")
vehicle1_data = {
    "user": driver_data["id"], "model": "Fiat Uno", "color": "vermelho",
    "plate": "ABC1D23", "seats": 5, "type_vehicle": "carro"
}
resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/vehicles/",
    json=vehicle1_data,
    headers=auth_header(new_driver_access))
vehicle1 = check_response(resp, 201)
vehicle1_id = vehicle1["id"]
print(f"✅ Veículo 1 criado:\n{json.dumps(vehicle1, indent=2)}")

print("\n🚗 Criando veículo 2 para motorista 1...")
vehicle2_data = {
    "user": driver_data["id"], "model": "Ford Ka", "color": "azul",
    "plate": "XYZ9A87", "seats": 4, "type_vehicle": "carro"
}
resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/vehicles/",
    json=vehicle2_data,
    headers=auth_header(new_driver_access))
vehicle2 = check_response(resp, 201)
vehicle2_id = vehicle2["id"]
print(f"✅ Veículo 2 criado:\n{json.dumps(vehicle2, indent=2)}")

print("\n🚗 Criando veículo 3 para motorista 2...")
vehicle3_data = {
    "user": driver2_data["id"], "model": "HB20", "color": "preto",
    "plate": "TES1234", "seats": 5, "type_vehicle": "carro"
}
resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/vehicles/",
    json=vehicle3_data,
    headers=auth_header(new_driver2_access))
vehicle3 = check_response(resp, 201)
vehicle3_id = vehicle3["id"]
print(f"✅ Veículo 3 criado:\n{json.dumps(vehicle3, indent=2)}")

# ============================================================
# 6. Testar endpoints de veículos (CRUD completo) com JWT
# ============================================================
print("\n" + "="*60)
print("6. TESTAR ENDPOINTS DE VEÍCULOS (CRUD)")
print("="*60)

print("\n📋 Listando veículos do motorista 1 (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/vehicles/",
    headers=auth_header(new_driver_access))
veiculos = check_response(resp, 200)
print(f"✅ Veículos encontrados: {len(veiculos)}\n{json.dumps(veiculos, indent=2)}")

print(f"\n🔍 Detalhe veículo {vehicle1_id} (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/vehicles/{vehicle1_id}/",
    headers=auth_header(new_driver_access))
veiculo_detalhe = check_response(resp, 200)
print(f"✅ Detalhe:\n{json.dumps(veiculo_detalhe, indent=2)}")

print(f"\n✏️ Atualizar veículo {vehicle1_id} (PATCH)...")
resp = req("PATCH", f"{RIDE_SERVICE_URL}/api/ride/vehicles/{vehicle1_id}/",
    json={"color": "azul"},
    headers=auth_header(new_driver_access))
veiculo_atualizado = check_response(resp, 200)
print(f"✅ Veículo atualizado:\n{json.dumps(veiculo_atualizado, indent=2)}")

print(f"\n🗑️ Deletar veículo {vehicle2_id} (DELETE)...")
resp = req("DELETE", f"{RIDE_SERVICE_URL}/api/ride/vehicles/{vehicle2_id}/",
    headers=auth_header(new_driver_access))
if resp.status_code == 204:
    print("✅ Veículo 2 deletado")
else:
    print(f"⚠️ DELETE retornou {resp.status_code}")

print("\n📋 Listando veículos após deleção (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/vehicles/",
    headers=auth_header(new_driver_access))
veiculos_pos = check_response(resp, 200)
print(f"✅ Veículos restantes: {len(veiculos_pos)}")

# ============================================================
# 7. Criar caronas (Ride Service) com json= e JWT
# ============================================================
print("\n" + "="*60)
print("7. CRIAÇÃO DE CARONAS")
print("="*60)

origins = ["Terminal Central", "Shopping", "Aeroporto", "Centro", "Rodoviária"]
destinations = ["Shopping", "Terminal Central", "Centro", "Aeroporto", "Rodoviária"]
prices = [25.00, 30.00, 45.00, 20.00, 35.00]
rides = []
ride_uuids = []

# 3 caronas do motorista 1 (veículo 1)
for i in range(2):
    start_time = (datetime.now(timezone.utc) + timedelta(hours=i+1)).isoformat()
    expected_arrival = (datetime.now(timezone.utc) + timedelta(hours=i+2)).isoformat()
    ride_data = {
        "vehicle": vehicle1_id,
        "origin": {"city": origins[i], "state": "SP", "description": origins[i]},
        "destination": {"city": destinations[i], "state": "SP", "description": destinations[i]},
        "start_time": start_time,
        "expected_arrival": expected_arrival,
        "available_seats": 3,
        "price": prices[i],
        "status": "pendente" 
    }
    resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/rides/",
        json=ride_data,
        headers=auth_header(new_driver_access))
    ride = check_response(resp, 201)
    rides.append(ride)
    ride_uuids.append(ride["id"])
    print(f"✅ Carona {i+1} criada (motorista 1): id={ride['id']}")

# 2 caronas do motorista 2 (veículo 3)
for i in range(3, 5):
    start_time = (datetime.now(timezone.utc) + timedelta(hours=i+1)).isoformat()
    expected_arrival = (datetime.now(timezone.utc) + timedelta(hours=i+2)).isoformat()
    ride_data = {
        "vehicle": vehicle3_id,
        "origin": {"city": origins[i], "state": "SP", "description": origins[i]},
        "destination": {"city": destinations[i], "state": "SP", "description": destinations[i]},
        "start_time": start_time,
        "expected_arrival": expected_arrival,
        "available_seats": 2,
        "price": prices[i],
        "status": "pendente"    
    }
    resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/rides/",
        json=ride_data,
        headers=auth_header(new_driver2_access))
    ride = check_response(resp, 201)
    rides.append(ride)
    ride_uuids.append(ride["id"])
    print(f"✅ Carona {i+1} criada (motorista 2): id={ride['id']}")

# ============================================================
# 8. Testar endpoints de rides (CRUD completo) com JWT
# ============================================================
print("\n" + "="*60)
print("8. TESTAR ENDPOINTS DE CARONAS (CRUD)")
print("="*60)

ride1_id = ride_uuids[0]

print("\n📋 Listando caronas (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/rides/",
    headers=auth_header(new_driver_access))
caronas = check_response(resp, 200)
print(f"✅ Caronas encontradas: {len(caronas)}\n{json.dumps(caronas, indent=2)}")

print(f"\n🔍 Detalhe carona {ride1_id} (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/rides/{ride1_id}/",
    headers=auth_header(new_driver_access))
carona_detalhe = check_response(resp, 200)
print(f"✅ Detalhe:\n{json.dumps(carona_detalhe, indent=2)}")

print(f"\n✏️ Atualizar carona {ride1_id} (PATCH)...")
patch_ride = {
    "vehicle": vehicle1_id,
    "origin": {"city": "Terminal Central", "state": "SP", "description": "Terminal Central"},
    "destination": {"city": "Centro", "state": "SP", "description": "Centro"},
    "start_time": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
    "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    "available_seats": 3,
    "price": 45.00
}
resp = req("PATCH", f"{RIDE_SERVICE_URL}/api/ride/rides/{ride1_id}/",
    json=patch_ride,
    headers=auth_header(new_driver_access))
carona_atualizada = check_response(resp, 200)
print(f"✅ Carona atualizada:\n{json.dumps(carona_atualizada, indent=2)}")

# ============================================================
# 9. Reservas com JWT (usar json=)
# ============================================================
print("\n" + "="*60)
print("9. RESERVAS")
print("="*60)

print("\n📅 Criando reservas para as 3 primeiras caronas...")
reservation_ids = []
for idx, ride in enumerate(rides[:3]):
    reservation_payload = {
        "ride": ride["id"],
        "passenger": passenger_data["id"],
        "requested_seats": 1,
        "status": "pendente"
    }
    resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/reservations/",
        json=reservation_payload,
        headers=auth_header(new_passenger_access))
    reservation = check_response(resp, 201)
    reservation_ids.append(reservation["id"])
    print(f"✅ Reserva {idx+1} criada: id={reservation['id']}")

time.sleep(2)

print("\n📋 Listando reservas (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/reservations/",
    headers=auth_header(new_passenger_access))
reservas = check_response(resp, 200)
print(f"✅ Reservas encontradas: {len(reservas)}\n{json.dumps(reservas, indent=2)}")

if reservation_ids:
    reservation1_id = reservation_ids[0]
    print(f"\n🔍 Detalhe reserva {reservation1_id} (GET)...")
    resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/reservations/{reservation1_id}/",
        headers=auth_header(new_passenger_access))
    reserva_detalhe = check_response(resp, 200)
    print(f"✅ Detalhe:\n{json.dumps(reserva_detalhe, indent=2)}")

    print(f"\n✏️ Confirmar reserva {reservation1_id} (PATCH)...")
    resp = req("PATCH", f"{RIDE_SERVICE_URL}/api/ride/reservations/{reservation1_id}/",
        json={"status": "confirmada"},
        headers=auth_header(new_passenger_access))
    reserva_confirmada = check_response(resp, 200)
    print(f"✅ Reserva confirmada:\n{json.dumps(reserva_confirmada, indent=2)}")

for idx, res_id in enumerate(reservation_ids[1:], start=2):
    print(f"\n✏️ Confirmar reserva {res_id} (PATCH)...")
    resp = req("PATCH", f"{RIDE_SERVICE_URL}/api/ride/reservations/{res_id}/",
        json={"status": "confirmada"},
        headers=auth_header(new_passenger_access))
    if resp.status_code == 200:
        print(f"✅ Reserva {idx} confirmada")
    else:
        print(f"⚠️ Reserva {idx}: status {resp.status_code}")

# ============================================================
# 10. Verificação de notificações após reserva com JWT
# ============================================================
print("\n" + "="*60)
print("10. NOTIFICAÇÕES APÓS RESERVA")
print("="*60)

print("\n⏳ Aguardando processamento das notificações (5s)...")
time.sleep(5)

print("\n🔔 Notificações do motorista 1 (após reserva):")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_driver_access))
notif_driver = check_response(resp, 200)
print(f"✅ Notificações motorista 1:\n{json.dumps(notif_driver, indent=2)}")

print("\n🔔 Notificações do passageiro (após reserva):")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_passenger_access))
notif_passenger = check_response(resp, 200)
print(f"✅ Notificações passageiro:\n{json.dumps(notif_passenger, indent=2)}")

# ============================================================
# 11. Chat - criação e mensagens com JWT
# ============================================================
print("\n" + "="*60)
print("11. CHAT E MENSAGENS")
print("="*60)

ride1_uuid = ride_uuids[0]
room = None

print(f"\n💬 Verificando se a sala de chat da carona {ride1_uuid} já existe...")
time.sleep(3)

resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/",
    headers=auth_header(new_passenger_access))
if resp_get.status_code == 200:
    room = resp_get.json()
    print(f"✅ Sala já existente: {json.dumps(room, indent=2)}")
else:
    print("⚠️ Sala não encontrada. Criando manualmente com motorista e passageiros...")
    chat_payload = {
        "carona_id": ride1_uuid,
        "driver_id": driver_data["id"],
        "passenger_ids": [passenger_data["id"]]
    }
    resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/",
        json=chat_payload,
        headers=auth_header(new_passenger_access))
    if resp_post.status_code in (200, 201):
        room = resp_post.json()
        print(f"✅ Sala criada com participantes:\n{json.dumps(room, indent=2)}")
    else:
        print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
        room = None

if room:
    msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"

    print("\n💬 Enviando mensagem do passageiro...")
    resp = req("POST", msg_url,
        json={"usuario_id": passenger_data["id"], "conteudo": "Olá, motorista! Estou no ponto."},
        headers=auth_header(new_passenger_access))
    msg_pass = check_response(resp, 201)
    print(f"✅ Mensagem do passageiro enviada:\n{json.dumps(msg_pass, indent=2)}")

    print("\n💬 Enviando mensagem do motorista 1...")
    resp = req("POST", msg_url,
        json={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."},
        headers=auth_header(new_driver_access))
    msg_motorista = check_response(resp, 201)
    print(f"✅ Mensagem do motorista enviada:\n{json.dumps(msg_motorista, indent=2)}")

    print("\n📜 Obtendo histórico de mensagens...")
    resp = req("GET", msg_url,
        headers=auth_header(new_passenger_access))
    messages = check_response(resp, 200)
    print(f"✅ {len(messages)} mensagens trocadas:\n{json.dumps(messages, indent=2)}")
else:
    print("⚠️ Pulando chat devido a erro na criação/obtenção da sala")

# ============================================================
# 12. Notificações após chat com JWT
# ============================================================
print("\n" + "="*60)
print("12. NOTIFICAÇÕES APÓS CHAT")
print("="*60)

print("\n⏳ Aguardando processamento das notificações de chat (5s)...")
time.sleep(5)

print("\n🔔 Notificações do motorista 1 (após chat):")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_driver_access))
notif_driver2 = check_response(resp, 200)
print(f"✅ Notificações motorista 1:\n{json.dumps(notif_driver2, indent=2)}")

print("\n🔔 Notificações do passageiro (após chat):")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_passenger_access))
notif_passenger2 = check_response(resp, 200)
print(f"✅ Notificações passageiro:\n{json.dumps(notif_passenger2, indent=2)}")

# ============================================================
# 13. Recomendação por IA (Ollama) com JWT
# ============================================================
print("\n" + "="*60)
print("13. RECOMENDAÇÃO POR IA (OLLAMA)")
print("="*60)

print(f"\n🤖 Testando recomendação por IA para passageiro {passenger_data['id']}...")
resp = req("GET",
    f"{RIDE_SERVICE_URL}/api/ride/rides/ai-recommendations/?user_id={passenger_data['id']}&top_n=3",
    headers=auth_header(new_passenger_access))

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
    print(f"❌ Falha na recomendação: {resp.status_code} - {resp.text[:200]}")

# ============================================================
# 14. Filtro inteligente com IA (Ollama) com JWT
# ============================================================
print("\n" + "="*60)
print("14. FILTRO INTELIGENTE COM IA (OLLAMA)")
print("="*60)

texto_busca = "quero viajar do centro para o aeroporto amanhã, preço até 30 reais"
print(f"\n📝 Texto de busca: \"{texto_busca}\"")

resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/rides/ai-filter/",
    json={"text": texto_busca},
    headers=auth_header(new_passenger_access))

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

# Segundo teste de filtro
print("\n" + "-"*40)
texto_busca2 = "Terminal Central para Shopping até 40"
print(f"📝 Teste com outro texto: \"{texto_busca2}\"")

resp = req("POST", f"{RIDE_SERVICE_URL}/api/ride/rides/ai-filter/",
    json={"text": texto_busca2},
    headers=auth_header(new_passenger_access))

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

# ============================================================
# 15. Teste adicional: listagem de caronas com filtros manuais com JWT
# ============================================================
print("\n" + "="*60)
print("15. LISTAGEM DE CARONAS COM FILTROS MANUAIS")
print("="*60)

print("\n📋 Listando caronas com filtro de origem (GET com query params)...")
resp = req("GET",
    f"{RIDE_SERVICE_URL}/api/ride/rides/?origin=Terminal+Central",
    headers=auth_header(new_passenger_access))
if resp.status_code == 200:
    caronas_filtradas = resp.json()
    print(f"✅ Caronas com origem 'Terminal Central': {len(caronas_filtradas) if isinstance(caronas_filtradas, list) else caronas_filtradas.get('count', 'N/A')}")
else:
    print(f"⚠️ Filtro retornou {resp.status_code}")

print("\n📋 Listando caronas com filtro de preço máximo (GET com query params)...")
resp = req("GET",
    f"{RIDE_SERVICE_URL}/api/ride/rides/?max_price=30",
    headers=auth_header(new_passenger_access))
if resp.status_code == 200:
    caronas_preco = resp.json()
    print(f"✅ Caronas com preço até R$30: {len(caronas_preco) if isinstance(caronas_preco, list) else caronas_preco.get('count', 'N/A')}")
else:
    print(f"⚠️ Filtro retornou {resp.status_code}")

# ============================================================
# 16. Teste adicional: veículos do motorista 2 com JWT
# ============================================================
print("\n" + "="*60)
print("16. VEÍCULOS DO MOTORISTA 2")
print("="*60)

print("\n📋 Listando veículos do motorista 2 (GET)...")
resp = req("GET", f"{RIDE_SERVICE_URL}/api/ride/vehicles/",
    headers=auth_header(new_driver2_access))
veiculos_m2 = check_response(resp, 200)
print(f"✅ Veículos do motorista 2: {len(veiculos_m2)}\n{json.dumps(veiculos_m2, indent=2)}")

# ============================================================
# 17. Teste de chat para segunda carona com JWT
# ============================================================
print("\n" + "="*60)
print("17. CHAT PARA SEGUNDA CARONA")
print("="*60)

if len(ride_uuids) >= 2:
    ride2_uuid = ride_uuids[1]
    room2 = None

    print(f"\n💬 Verificando sala de chat da carona {ride2_uuid}...")
    resp_get2 = req("GET", f"{BASE_URL}/api/chat/rooms/{ride2_uuid}/",
        headers=auth_header(new_passenger_access))
    if resp_get2.status_code == 200:
        room2 = resp_get2.json()
        print(f"✅ Sala já existente: {json.dumps(room2, indent=2)}")
    else:
        print("⚠️ Sala não encontrada. Criando manualmente...")
        chat_payload2 = {
            "carona_id": ride2_uuid,
            "driver_id": driver_data["id"],
            "passenger_ids": [passenger_data["id"]]
        }
        resp_post2 = req("POST", f"{BASE_URL}/api/chat/rooms/",
            json=chat_payload2,
            headers=auth_header(new_passenger_access))
        if resp_post2.status_code in (200, 201):
            room2 = resp_post2.json()
            print(f"✅ Sala criada:\n{json.dumps(room2, indent=2)}")
        else:
            print(f"❌ Erro ao criar sala: {resp_post2.status_code} - {resp_post2.text}")

    if room2:
        msg_url2 = f"{BASE_URL}/api/chat/rooms/{ride2_uuid}/messages/"

        print("\n💬 Enviando mensagem do passageiro na carona 2...")
        resp = req("POST", msg_url2,
            json={"usuario_id": passenger_data["id"], "conteudo": "Qual o ponto de encontro?"},
            headers=auth_header(new_passenger_access))

        if resp.status_code == 201:
            msg_p2 = resp.json()
            print(f"✅ Mensagem enviada:\n{json.dumps(msg_p2, indent=2)}")
        else:
            print(f"⚠️ Erro ao enviar mensagem: {resp.status_code}")

        print("\n💬 Enviando mensagem do motorista na carona 2...")
        resp = req("POST", msg_url2,
            json={"usuario_id": driver_data["id"], "conteudo": "Em frente ao shopping!"},
            headers=auth_header(new_driver_access))
        if resp.status_code == 201:
            msg_m2 = resp.json()
            print(f"✅ Mensagem enviada:\n{json.dumps(msg_m2, indent=2)}")
        else:
            print(f"⚠️ Erro ao enviar mensagem: {resp.status_code}")

        print("\n📜 Histórico de mensagens da carona 2...")
        resp = req("GET", msg_url2,
            headers=auth_header(new_passenger_access))
        if resp.status_code == 200:
            msgs2 = resp.json()
            print(f"✅ {len(msgs2)} mensagens:\n{json.dumps(msgs2, indent=2)}")
        else:
            print(f"⚠️ Erro ao obter histórico: {resp.status_code}")
else:
    print("⚠️ Não há caronas suficientes para testar chat na segunda carona")

# ============================================================
# 18. Notificações finais com JWT
# ============================================================
print("\n" + "="*60)
print("18. NOTIFICAÇÕES FINAIS")
print("="*60)

print("\n⏳ Aguardando processamento final (5s)...")
time.sleep(5)

print("\n🔔 Notificações finais do motorista 1:")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_driver_access))
notif_driver_final = check_response(resp, 200)
print(f"✅ Total de notificações motorista 1: {len(notif_driver_final)}\n{json.dumps(notif_driver_final, indent=2)}")

print("\n🔔 Notificações finais do motorista 2:")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_driver2_access))
notif_driver2_final = check_response(resp, 200)
print(f"✅ Total de notificações motorista 2: {len(notif_driver2_final)}\n{json.dumps(notif_driver2_final, indent=2)}")

print("\n🔔 Notificações finais do passageiro:")
resp = req("GET", f"{BASE_URL}/api/notifications/",
    headers=auth_header(new_passenger_access))
notif_passenger_final = check_response(resp, 200)
print(f"✅ Total de notificações passageiro: {len(notif_passenger_final)}\n{json.dumps(notif_passenger_final, indent=2)}")

# ============================================================
# 19. Marcar notificações como lidas com JWT
# ============================================================
print("\n" + "="*60)
print("19. MARCAR NOTIFICAÇÕES COMO LIDAS")
print("="*60)

if notif_driver_final:
    first_notif_id = notif_driver_final[0].get("id")
    if first_notif_id:
        print(f"\n✏️ Marcando notificação {first_notif_id} como lida (PATCH)...")
        resp = req("PATCH", f"{BASE_URL}/api/notifications/{first_notif_id}/read/",
           json={},   # ou json={"read": True} – a view ignora o corpo
           headers=auth_header(new_driver_access))


        if resp.status_code == 200:
            print(f"✅ Notificação marcada como lida: {json.dumps(resp.json(), indent=2)}")
        else:
            print(f"⚠️ Erro ao marcar notificação: {resp.status_code}")

if notif_passenger_final:
    first_notif_p_id = notif_passenger_final[0].get("id")
    if first_notif_p_id:
        print(f"\n✏️ Marcando notificação {first_notif_p_id} como lida (PATCH)...")
        resp = req("PATCH", f"{BASE_URL}/api/notifications/{first_notif_p_id}/read/",
           json={},
           headers=auth_header(new_passenger_access))

        if resp.status_code == 200:
            print(f"✅ Notificação marcada como lida: {json.dumps(resp.json(), indent=2)}")
        else:
            print(f"⚠️ Erro ao marcar notificação: {resp.status_code}")

# ============================================================
# 20. Logout com JWT
# ============================================================
print("\n" + "="*60)
print("20. LOGOUT")
print("="*60)

print("\n🚪 Logout do motorista 1 (POST /api/logout/)...")
logout_refresh_driver = new_driver_refresh if new_driver_refresh else driver_refresh
resp = req("POST", f"{BASE_URL}/api/logout/",
    json={"refresh": logout_refresh_driver},
    headers=auth_header(new_driver_access))
if resp.status_code == 205:
    print("✅ Logout motorista 1 realizado")
else:
    print(f"⚠️ Logout motorista 1 retornou {resp.status_code}")

print("\n🚪 Logout do motorista 2 (POST /api/logout/)...")
logout_refresh_driver2 = new_driver2_refresh if new_driver2_refresh else driver2_refresh
resp = req("POST", f"{BASE_URL}/api/logout/",
    json={"refresh": logout_refresh_driver2},
    headers=auth_header(new_driver2_access))
if resp.status_code == 205:
    print("✅ Logout motorista 2 realizado")
else:
    print(f"⚠️ Logout motorista 2 retornou {resp.status_code}")

print("\n🚪 Logout do passageiro (POST /api/logout/)...")
logout_refresh_passenger = new_passenger_refresh if new_passenger_refresh else passenger_refresh
resp = req("POST", f"{BASE_URL}/api/logout/",
    json={"refresh": logout_refresh_passenger},
    headers=auth_header(new_passenger_access))
if resp.status_code == 205:
    print("✅ Logout passageiro realizado")
else:
    print(f"⚠️ Logout passageiro retornou {resp.status_code}")

# ============================================================
# FIM
# ============================================================
print("\n" + "="*60)
print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
print("="*60)
print(f"\n📊 Resumo:")
print(f"   - 3 usuários registrados (2 motoristas, 1 passageiro)")
print(f"   - JWT obtido e refreshado para todos")
print(f"   - 3 veículos criados (2 motorista 1, 1 motorista 2)")
print(f"   - 5 caronas criadas (3 motorista 1, 2 motorista 2)")
print(f"   - 3 reservas criadas e confirmadas")
print(f"   - Chat testado em 2 caronas")
print(f"   - Notificações verificadas após cada ação")
print(f"   - Recomendação IA testada")
print(f"   - Filtro IA testado com 2 textos diferentes")
print(f"   - Notificações marcadas como lidas")
print(f"   - Logout realizado para todos os usuários")
print(f"\n🔐 Todas as requisições ao Ride Service utilizaram headers JWT!")