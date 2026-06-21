# # import requests
# # import uuid
# # import random
# # import time
# # import json
# # import os
# # import tempfile
# # from datetime import datetime, timedelta, timezone
# # from io import BytesIO

# # BASE_URL = "http://localhost:8000"

# # # ------------------------------------------------------------
# # # Utilitários
# # # ------------------------------------------------------------
# # def gerar_cpf():
# #     def digito(digs):
# #         s = sum(d * (len(digs)+1 - i) for i, d in enumerate(digs))
# #         d = 11 - (s % 11)
# #         return d if d < 10 else 0
# #     base = [random.randint(0, 9) for _ in range(9)]
# #     base.append(digito(base))
# #     base.append(digito(base))
# #     cpf_str = ''.join(map(str, base))
# #     return f'{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}'

# # def random_email():
# #     return f"test_{uuid.uuid4().hex[:8]}@example.com"

# # def check_response(resp, success_code=200, silent=False):
# #     if resp.status_code != success_code:
# #         if not silent:
# #             print(f"❌ Erro {resp.status_code}: {resp.text[:200]}")
# #         return None
# #     return resp.json()

# # def get_tokens(email, password):
# #     resp = requests.post(f"{BASE_URL}/api/login/", json={"email": email, "password": password})
# #     data = check_response(resp)
# #     if data is None:
# #         return None, None
# #     return data["access"], data["refresh"]

# # def auth_header(token):
# #     return {"Authorization": f"Bearer {token}"}

# # def req(method, url, **kwargs):
# #     headers = kwargs.get("headers")
# #     masked_headers = None
# #     if headers and "Authorization" in headers:
# #         token = headers["Authorization"].split()[1]
# #         masked = token[:10] + "..." + token[-10:] if len(token) > 20 else token
# #         masked_headers = {"Authorization": f"Bearer {masked}"}
# #     else:
# #         masked_headers = headers

# #     body = None
# #     if "data" in kwargs:
# #         body = kwargs["data"]
# #     elif "json" in kwargs:
# #         body = kwargs["json"]

# #     print(f"\n➡️ {method} {url}")
# #     if masked_headers:
# #         print(f"   headers: {json.dumps(masked_headers, indent=2)}")
# #     if body:
# #         print(f"   body:\n{json.dumps(body, indent=2, ensure_ascii=False)}")
    
# #     resp = requests.request(method, url, **kwargs)
# #     print(f"⬅️ {resp.status_code}")
# #     return resp

# # def criar_arquivo_foto():
# #     import base64
# #     png_data = base64.b64decode(
# #         "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
# #     )
# #     return BytesIO(png_data)

# # # ------------------------------------------------------------
# # # 1. Registrar usuários
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("1. REGISTRO DE USUÁRIOS")
# # print("="*60)

# # driver_email = random_email()
# # passenger_email = random_email()
# # password = "Teste@123"

# # print("\n📝 Registrando motorista...")
# # resp = req("POST", f"{BASE_URL}/api/register/", data={
# #     "email": driver_email, "nome": "Motorista Silva", "password": password,
# #     "cpf": gerar_cpf(), "telefone": "11999990001", "tipo_usuario": "Motorista",
# # })
# # driver_data = check_response(resp, 201)
# # if driver_data is None:
# #     print("❌ Falha no registro do motorista. Abortando.")
# #     exit(1)
# # print(f"✅ Motorista registrado:\n{json.dumps(driver_data, indent=2)}")

# # print("\n📝 Registrando passageiro...")
# # resp = req("POST", f"{BASE_URL}/api/register/", data={
# #     "email": passenger_email, "nome": "Passageiro Santos", "password": password,
# #     "cpf": gerar_cpf(), "telefone": "11999990002", "tipo_usuario": "Passageiro",
# # })
# # passenger_data = check_response(resp, 201)
# # if passenger_data is None:
# #     print("❌ Falha no registro do passageiro. Abortando.")
# #     exit(1)
# # print(f"✅ Passageiro registrado:\n{json.dumps(passenger_data, indent=2)}")

# # print("\n⏳ Aguardando sincronização Kafka (5s)...")
# # time.sleep(5)

# # # ------------------------------------------------------------
# # # 2. Login
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("2. LOGIN E TOKENS")
# # print("="*60)

# # print("\n🔐 Fazendo login...")
# # driver_access, driver_refresh = get_tokens(driver_email, password)
# # passenger_access, passenger_refresh = get_tokens(passenger_email, password)
# # if driver_access is None or passenger_access is None:
# #     print("❌ Falha no login. Abortando.")
# #     exit(1)
# # print("✅ Tokens obtidos")

# # # ------------------------------------------------------------
# # # 3. Profile e refresh
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("3. PERFIL E REFRESH TOKEN")
# # print("="*60)

# # print("\n✏️ Atualizando perfil (PATCH /api/profile/)...")
# # foto = criar_arquivo_foto()
# # files = {'foto': ('foto.png', foto, 'image/png')}
# # resp = req("PATCH", f"{BASE_URL}/api/profile/", data={"telefone": "11999999999"}, files=files, headers=auth_header(driver_access))
# # if check_response(resp, 200) is not None:
# #     print("✅ Perfil atualizado com foto")
# # else:
# #     print("⚠️ Falha ao atualizar perfil (pode ser que foto não seja aceita no PATCH)")

# # print("\n🔄 Refresh token (POST /api/token/refresh/)...")
# # resp = req("POST", f"{BASE_URL}/api/token/refresh/", json={"refresh": driver_refresh})
# # tokens = check_response(resp, 200)
# # if tokens is not None:
# #     new_driver_access = tokens["access"]
# #     new_driver_refresh = tokens.get("refresh", driver_refresh)
# #     print("✅ Token refresh OK")
# # else:
# #     print("❌ Falha no refresh token. Usando token antigo.")
# #     new_driver_access = driver_access
# #     new_driver_refresh = driver_refresh

# # # ------------------------------------------------------------
# # # 4. Criar veículos
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("4. CRIAÇÃO DE VEÍCULOS")
# # print("="*60)

# # print("\n🚗 Criando veículo 1...")
# # vehicle_data = {
# #     "user": driver_data["id"], "model": "Fiat Uno", "color": "vermelho",
# #     "plate": "ABC1D23", "seats": 5,
# #     "type_vehicle": "carro" 
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle_data, headers=auth_header(new_driver_access))
# # vehicle1 = check_response(resp, 201)
# # if vehicle1 is None:
# #     print("❌ Falha ao criar veículo 1. Abortando.")
# #     exit(1)
# # vehicle1_id = vehicle1["id"]
# # print(f"✅ Veículo 1 criado:\n{json.dumps(vehicle1, indent=2)}")

# # print("\n🚗 Criando veículo 2...")
# # vehicle2_data = {
# #     "user": driver_data["id"], "model": "Ford Ka", "color": "azul",
# #     "plate": "XYZ9A87", "seats": 4,
# #     "type_vehicle": "carro" 
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle2_data, headers=auth_header(new_driver_access))
# # vehicle2 = check_response(resp, 201)
# # if vehicle2 is None:
# #     print("❌ Falha ao criar veículo 2. Abortando.")
# #     exit(1)
# # vehicle2_id = vehicle2["id"]
# # print(f"✅ Veículo 2 criado:\n{json.dumps(vehicle2, indent=2)}")

# # # ------------------------------------------------------------
# # # 5. Testes de veículos
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("5. TESTES DE VEÍCULOS (CRUD, SOFT DELETE, VALIDAÇÕES)")
# # print("="*60)

# # print("\n📋 Listando veículos (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/vehicles/", headers=auth_header(new_driver_access))
# # veiculos = check_response(resp, 200)
# # if veiculos is not None:
# #     print(f"✅ Veículos encontrados: {len(veiculos)}\n{json.dumps(veiculos, indent=2)}")
# # else:
# #     print("⚠️ Falha ao listar veículos")

# # print(f"\n🔍 Detalhe veículo {vehicle1_id} (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", headers=auth_header(new_driver_access))
# # veiculo_detalhe = check_response(resp, 200)
# # if veiculo_detalhe is not None:
# #     print(f"✅ Detalhe:\n{json.dumps(veiculo_detalhe, indent=2)}")
# # else:
# #     print("⚠️ Falha ao obter detalhe do veículo")

# # print(f"\n✏️ Atualizar veículo {vehicle1_id} (PATCH)...")
# # resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", json={"color": "verde"}, headers=auth_header(new_driver_access))
# # veiculo_atualizado = check_response(resp, 200)
# # if veiculo_atualizado is not None:
# #     print(f"✅ Veículo atualizado:\n{json.dumps(veiculo_atualizado, indent=2)}")
# # else:
# #     print("⚠️ Falha ao atualizar veículo")

# # print(f"\n🗑️ Deletar veículo {vehicle2_id} (DELETE) - soft delete...")
# # resp = req("DELETE", f"{BASE_URL}/api/ride/vehicles/{vehicle2_id}/", headers=auth_header(new_driver_access))
# # if resp.status_code == 204:
# #     print("✅ Veículo 2 deletado (soft delete)")
# #     resp_list = req("GET", f"{BASE_URL}/api/ride/vehicles/", headers=auth_header(new_driver_access))
# #     lista = check_response(resp_list, 200)
# #     if lista is not None:
# #         ids = [v["id"] for v in lista]
# #         if vehicle2_id not in ids:
# #             print("✅ Veículo 2 não aparece na listagem (soft delete funcionando)")
# #         else:
# #             print("⚠️ Veículo 2 ainda aparece na listagem (soft delete pode não estar funcionando)")
# # else:
# #     print(f"⚠️ DELETE retornou {resp.status_code}")

# # print("\n🧪 Teste de validação: tentar criar moto com 4 assentos (deve falhar)...")
# # vehicle_invalido = {
# #     "user": driver_data["id"], "model": "Moto X", "color": "preto",
# #     "plate": "MOTO123", "seats": 4,
# #     "type_vehicle": "moto"
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle_invalido, headers=auth_header(new_driver_access))
# # if resp.status_code == 400:
# #     print("✅ Validação funcionou: moto com mais de 2 assentos foi rejeitada.")
# # else:
# #     print(f"⚠️ Validação falhou: esperado 400, obtido {resp.status_code}")

# # # ------------------------------------------------------------
# # # 6. Criar caronas
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("6. CRIAÇÃO DE CARONAS")
# # print("="*60)

# # print("\n🚕 Criando carona 1...")
# # start_time = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
# # expected_arrival = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
# # ride_data = {
# #     "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "Aeroporto",
# #     "start_time": start_time, "expected_arrival": expected_arrival,
# #     "available_seats": 3, "status": "pendente", "price": 45.00
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride_data, headers=auth_header(new_driver_access))
# # ride1 = check_response(resp, 201)
# # if ride1 is None:
# #     print("❌ Falha ao criar carona 1. Abortando.")
# #     exit(1)
# # ride1_id = ride1["id"]
# # ride1_uuid = ride1["uuid"]
# # print(f"✅ Carona 1 criada:\n{json.dumps(ride1, indent=2)}")

# # print("\n🚕 Criando carona 2...")
# # ride2_data = {
# #     "vehicle": vehicle1_id, "origin": "Centro", "destination": "Shopping",
# #     "start_time": (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
# #     "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
# #     "available_seats": 2, "status": "pendente", "price": 20.00
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride2_data, headers=auth_header(new_driver_access))
# # ride2 = check_response(resp, 201)
# # if ride2 is None:
# #     print("❌ Falha ao criar carona 2. Abortando.")
# #     exit(1)
# # ride2_id = ride2["id"]
# # print(f"✅ Carona 2 criada:\n{json.dumps(ride2, indent=2)}")

# # # ------------------------------------------------------------
# # # 7. Testes de caronas (listagem, detalhe, atualização, validações)
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("7. TESTES DE CARONAS (CRUD, FILTROS, VALIDAÇÕES)")
# # print("="*60)

# # print("\n📋 Listando caronas (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/rides/", headers=auth_header(new_driver_access))
# # caronas = check_response(resp, 200)
# # if caronas is not None:
# #     print(f"✅ Caronas encontradas: {len(caronas)}\n{json.dumps(caronas, indent=2)}")
# # else:
# #     print("⚠️ Falha ao listar caronas")

# # print(f"\n🔍 Detalhe carona {ride1_id} (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/rides/{ride1_id}/", headers=auth_header(new_driver_access))
# # carona_detalhe = check_response(resp, 200)
# # if carona_detalhe is not None:
# #     print(f"✅ Detalhe:\n{json.dumps(carona_detalhe, indent=2)}")
# # else:
# #     print("⚠️ Falha ao obter detalhe da carona")

# # print(f"\n✏️ Atualizar carona {ride1_id} (PATCH)...")
# # patch_ride = {
# #     "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "centro",
# #     "start_time": start_time, "expected_arrival": expected_arrival,
# #     "available_seats": 3, "status": "pendente", "price": "45.00"
# # }
# # resp = req("PATCH", f"{BASE_URL}/api/ride/rides/{ride1_id}/", json=patch_ride, headers=auth_header(new_driver_access))
# # carona_atualizada = check_response(resp, 200)
# # if carona_atualizada is not None:
# #     print(f"✅ Carona atualizada:\n{json.dumps(carona_atualizada, indent=2)}")
# # else:
# #     print("⚠️ Falha ao atualizar carona")

# # print("\n🧪 Teste de validação: criar carona com assentos > veículo (deve falhar)...")
# # ride_invalida = {
# #     "vehicle": vehicle1_id, "origin": "Teste", "destination": "Falha",
# #     "start_time": (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
# #     "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
# #     "available_seats": 10,
# #     "status": "pendente", "price": 10.00
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride_invalida, headers=auth_header(new_driver_access))
# # if resp.status_code == 400:
# #     print("✅ Validação funcionou: assentos maiores que veículo rejeitado.")
# # else:
# #     print(f"⚠️ Validação falhou: esperado 400, obtido {resp.status_code}")

# # # ------------------------------------------------------------
# # # Filtros (corrigidos para usar strftime com Z)
# # # ------------------------------------------------------------
# # print("\n🔎 Testando filtros do endpoint /api/ride/rides/")

# # # Define uma função auxiliar para gerar timestamps com Z
# # def utc_iso_z(dt):
# #     return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

# # filtros_teste = [
# #     ("Filtro por origin (Terminal Central)", "origin=Terminal Central"),
# #     ("Filtro por destination (Shopping)", "destination=Shopping"),
# #     ("Filtro por status (pendente)", "status=pendente"),
# #     ("Filtro price_min (30)", "price_min=30"),
# #     ("Filtro price_max (30)", "price_max=30"),
# #     ("Filtro available_seats_min (3)", "available_seats_min=3"),
# #     ("Filtro available_seats_max (2)", "available_seats_max=2"),
# #     ("Filtro start_time_after (daqui a 1 hora)", f"start_time_after={utc_iso_z(datetime.now(timezone.utc) + timedelta(hours=1))}"),
# #     ("Filtro start_time_before (daqui a 6 horas)", f"start_time_before={utc_iso_z(datetime.now(timezone.utc) + timedelta(hours=6))}"),
# #     ("Filtro vehicle_type (carro)", "vehicle_type=carro"),
# #     ("Filtro vehicle_model (Fiat)", "vehicle_model=Fiat"),
# #     ("Filtro vehicle_seats_min (4)", "vehicle_seats_min=4"),
# #     ("Busca textual por 'Terminal'", "search=Terminal"),
# #     ("Ordenação por preço crescente", "ordering=price"),
# #     ("Ordenação por preço decrescente", "ordering=-price"),
# # ]

# # for desc, query in filtros_teste:
# #     url = f"{BASE_URL}/api/ride/rides/?{query}"
# #     print(f"\n--- {desc} ---")
# #     resp = req("GET", url, headers=auth_header(new_driver_access))
# #     if resp.status_code == 200:
# #         data = resp.json()
# #         print(f"✅ Retornou {len(data)} caronas")
# #         if data:
# #             print(json.dumps(data[:2], indent=2))
# #     else:
# #         print(f"❌ Falha ao aplicar filtro: {resp.status_code}")

# # # ------------------------------------------------------------
# # # 8. Reservas e notificações
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("8. RESERVAS E NOTIFICAÇÕES")
# # print("="*60)

# # print("\n📅 Criando reserva...")
# # reservation_data = {
# #     "ride": ride1_id, "passenger": passenger_data["id"],
# #     "requested_seats": 2, "status": "pendente"
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/reservations/", json=reservation_data, headers=auth_header(passenger_access))
# # reservation1 = check_response(resp, 201)
# # if reservation1 is None:
# #     print("❌ Falha ao criar reserva. Abortando.")
# #     exit(1)
# # reservation1_id = reservation1["id"]
# # print(f"✅ Reserva criada:\n{json.dumps(reservation1, indent=2)}")

# # print("\n📋 Listando reservas (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/reservations/", headers=auth_header(passenger_access))
# # reservas = check_response(resp, 200)
# # if reservas is not None:
# #     print(f"✅ Reservas encontradas: {len(reservas)}\n{json.dumps(reservas, indent=2)}")
# # else:
# #     print("⚠️ Falha ao listar reservas")

# # print(f"\n🔍 Detalhe reserva {reservation1_id} (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", headers=auth_header(passenger_access))
# # reserva_detalhe = check_response(resp, 200)
# # if reserva_detalhe is not None:
# #     print(f"✅ Detalhe:\n{json.dumps(reserva_detalhe, indent=2)}")
# # else:
# #     print("⚠️ Falha ao obter detalhe da reserva")

# # print(f"\n✏️ Confirmar reserva {reservation1_id} (PATCH)...")
# # resp = req("PATCH", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", json={"status": "confirmada"}, headers=auth_header(new_driver_access))
# # reserva_confirmada = check_response(resp, 200)
# # if reserva_confirmada is not None:
# #     print(f"✅ Reserva confirmada:\n{json.dumps(reserva_confirmada, indent=2)}")
# # else:
# #     print("⚠️ Falha ao confirmar reserva")

# # print("\n⏳ Aguardando processamento das notificações (5s)...")
# # time.sleep(5)

# # print("\n--- Notificações do motorista (após reserva) ---")
# # resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
# # notificacoes_motorista = check_response(resp, 200)
# # if notificacoes_motorista is not None:
# #     print(json.dumps(notificacoes_motorista, indent=2))
# # else:
# #     print("⚠️ Falha ao obter notificações do motorista")

# # print("\n--- Notificações do passageiro (após reserva) ---")
# # resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
# # notificacoes_passageiro = check_response(resp, 200)
# # if notificacoes_passageiro is not None:
# #     print(json.dumps(notificacoes_passageiro, indent=2))
# # else:
# #     print("⚠️ Falha ao obter notificações do passageiro")

# # if notificacoes_motorista and len(notificacoes_motorista) > 0:
# #     notif_id = notificacoes_motorista[0]["id"]
# #     print(f"\n📌 Marcando notificação {notif_id} como lida...")
# #     resp = req("PATCH", f"{BASE_URL}/api/notifications/{notif_id}/read/", headers=auth_header(new_driver_access))
# #     if resp.status_code == 200:
# #         print("✅ Notificação marcada como lida")
# #     else:
# #         print(f"⚠️ Falha ao marcar notificação: {resp.status_code}")

# # print("\n🧪 Teste de validação: reservar mais vagas que disponíveis (deve falhar)...")
# # reserva_invalida = {
# #     "ride": ride1_id, "passenger": passenger_data["id"],
# #     "requested_seats": 10, "status": "pendente"
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/reservations/", json=reserva_invalida, headers=auth_header(passenger_access))
# # if resp.status_code == 400:
# #     print("✅ Validação funcionou: reserva com vagas insuficientes rejeitada.")
# # else:
# #     print(f"⚠️ Validação falhou: esperado 400, obtido {resp.status_code}")

# # # ------------------------------------------------------------
# # # 9. Avaliações
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("9. AVALIAÇÕES")
# # print("="*60)

# # print("\n⭐ Criando avaliação do passageiro para o motorista...")
# # rating_data = {
# #     "reservation": reservation1_id,
# #     "evaluator": passenger_data["id"],
# #     "evaluated": driver_data["id"],
# #     "score": 5
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/ratings/", json=rating_data, headers=auth_header(passenger_access))
# # rating1 = check_response(resp, 201)
# # if rating1 is not None:
# #     rating1_id = rating1["id"]
# #     print(f"✅ Avaliação criada:\n{json.dumps(rating1, indent=2)}")
# # else:
# #     print("⚠️ Falha ao criar avaliação")

# # print("\n📋 Listando avaliações (GET)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/ratings/", headers=auth_header(passenger_access))
# # ratings = check_response(resp, 200)
# # if ratings is not None:
# #     print(f"✅ Avaliações encontradas: {len(ratings)}\n{json.dumps(ratings, indent=2)}")
# # else:
# #     print("⚠️ Falha ao listar avaliações")

# # if rating1 is not None:
# #     print(f"\n🔍 Detalhe avaliação {rating1_id} (GET)...")
# #     resp = req("GET", f"{BASE_URL}/api/ride/ratings/{rating1_id}/", headers=auth_header(passenger_access))
# #     rating_detalhe = check_response(resp, 200)
# #     if rating_detalhe is not None:
# #         print(f"✅ Detalhe:\n{json.dumps(rating_detalhe, indent=2)}")
# #     else:
# #         print("⚠️ Falha ao obter detalhe da avaliação")

# #     print(f"\n✏️ Atualizar avaliação {rating1_id} (PATCH)...")
# #     resp = req("PATCH", f"{BASE_URL}/api/ride/ratings/{rating1_id}/", json={"score": 4}, headers=auth_header(passenger_access))
# #     rating_atualizado = check_response(resp, 200)
# #     if rating_atualizado is not None:
# #         print(f"✅ Avaliação atualizada:\n{json.dumps(rating_atualizado, indent=2)}")
# #     else:
# #         print("⚠️ Falha ao atualizar avaliação")

# # print("\n🧪 Teste de validação: avaliar a si mesmo (deve falhar)...")
# # rating_invalida = {
# #     "reservation": reservation1_id,
# #     "evaluator": passenger_data["id"],
# #     "evaluated": passenger_data["id"],
# #     "score": 5
# # }
# # resp = req("POST", f"{BASE_URL}/api/ride/ratings/", json=rating_invalida, headers=auth_header(passenger_access))
# # if resp.status_code == 400:
# #     print("✅ Validação funcionou: autoavaliação rejeitada.")
# # else:
# #     print(f"⚠️ Validação falhou: esperado 400, obtido {resp.status_code}")

# # # ------------------------------------------------------------
# # # 10. Chat e notificações
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("10. CHAT E NOTIFICAÇÕES DE CHAT")
# # print("="*60)

# # print("\n💬 Verificando se a sala de chat foi criada automaticamente (via Kafka) após confirmação da carona...")
# # time.sleep(5)
# # resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/", headers=auth_header(passenger_access))
# # if resp_get.status_code == 200:
# #     room = resp_get.json()
# #     print(f"✅ Sala encontrada (criada automaticamente):\n{json.dumps(room, indent=2)}")
# # else:
# #     print("⚠️ Sala não encontrada. Criando manualmente para continuar os testes...")
# #     chat_payload = {
# #         "carona_id": ride1_uuid,
# #         "driver_id": driver_data["id"],
# #         "passenger_ids": [passenger_data["id"]]
# #     }
# #     resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", json=chat_payload, headers=auth_header(passenger_access))
# #     if resp_post.status_code in (200, 201):
# #         room = resp_post.json()
# #         print(f"✅ Sala criada manualmente: {json.dumps(room, indent=2)}")
# #     else:
# #         print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
# #         room = None

# # if room:
# #     msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
# #     print("\n💬 Enviando mensagem do motorista...")
# #     resp = req("POST", msg_url, json={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
# #     msg_motorista = check_response(resp, 201)
# #     if msg_motorista is not None:
# #         print(f"✅ Mensagem do motorista enviada:\n{json.dumps(msg_motorista, indent=2)}")
# #     else:
# #         print("⚠️ Falha ao enviar mensagem do motorista")

# #     print("\n💬 Enviando mensagem do passageiro...")
# #     resp = req("POST", msg_url, json={"usuario_id": passenger_data["id"], "conteudo": "Olá, estou no ponto!"}, headers=auth_header(passenger_access))
# #     msg_passageiro = check_response(resp, 201)
# #     if msg_passageiro is not None:
# #         print(f"✅ Mensagem do passageiro enviada:\n{json.dumps(msg_passageiro, indent=2)}")
# #     else:
# #         print("⚠️ Falha ao enviar mensagem do passageiro")

# #     print("\n📜 Obtendo histórico de mensagens...")
# #     resp = req("GET", msg_url, headers=auth_header(passenger_access))
# #     messages = check_response(resp, 200)
# #     if messages is not None:
# #         print(f"✅ {len(messages)} mensagens trocadas:\n{json.dumps(messages, indent=2)}")
# #     else:
# #         print("⚠️ Falha ao obter mensagens")

# #     print("\n⏳ Aguardando processamento das notificações do chat (5s)...")
# #     time.sleep(5)

# #     print("\n--- Notificações do motorista (agora com chat) ---")
# #     resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(new_driver_access))
# #     notificacoes_motorista_chat = check_response(resp, 200)
# #     if notificacoes_motorista_chat is not None:
# #         print(json.dumps(notificacoes_motorista_chat, indent=2))
# #     else:
# #         print("⚠️ Falha ao obter notificações do motorista")

# #     print("\n--- Notificações do passageiro (agora com chat) ---")
# #     resp = req("GET", f"{BASE_URL}/api/notifications/", headers=auth_header(passenger_access))
# #     notificacoes_passageiro_chat = check_response(resp, 200)
# #     if notificacoes_passageiro_chat is not None:
# #         print(json.dumps(notificacoes_passageiro_chat, indent=2))
# #     else:
# #         print("⚠️ Falha ao obter notificações do passageiro")
# # else:
# #     print("⚠️ Pulando chat devido a erro na criação/obtenção da sala")

# # # ------------------------------------------------------------
# # # 11. Testes de regras de negócio
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("11. TESTES DE REGRAS DE NEGÓCIO (LIMITES, SUSPENSÃO, CANCELAMENTO)")
# # print("="*60)

# # print("\n📝 Registrando segundo passageiro para testes de limite...")
# # passenger2_email = random_email()
# # resp = req("POST", f"{BASE_URL}/api/register/", data={
# #     "email": passenger2_email, "nome": "Passageiro Teste Limite", "password": password,
# #     "cpf": gerar_cpf(), "telefone": "11999990003", "tipo_usuario": "Passageiro",
# # })
# # passenger2_data = check_response(resp, 201)
# # if passenger2_data is None:
# #     print("⚠️ Falha ao registrar segundo passageiro. Pulando testes de limite.")
# # else:
# #     print(f"✅ Segundo passageiro registrado:\n{json.dumps(passenger2_data, indent=2)}")
# #     pass2_access, _ = get_tokens(passenger2_email, password)
# #     if pass2_access is None:
# #         print("⚠️ Falha ao fazer login do segundo passageiro. Pulando testes de limite.")
# #     else:
# #         print("\n🧪 Teste de limite de reservas ativas (máximo 3)...")
# #         for i in range(1, 5):
# #             reserva = {
# #                 "ride": ride1_id, "passenger": passenger2_data["id"],
# #                 "requested_seats": 1, "status": "pendente"
# #             }
# #             resp = req("POST", f"{BASE_URL}/api/ride/reservations/", json=reserva, headers=auth_header(pass2_access))
# #             if i <= 3:
# #                 if resp.status_code == 201:
# #                     print(f"✅ Reserva {i} criada (esperado)")
# #                 else:
# #                     print(f"⚠️ Reserva {i} falhou inesperadamente: {resp.status_code}")
# #             else:
# #                 if resp.status_code == 400:
# #                     print(f"✅ Reserva {i} rejeitada (limite de 3 ativas) - correto")
# #                 else:
# #                     print(f"⚠️ Reserva {i} deveria ser rejeitada, mas retornou {resp.status_code}")

# #         resp = req("GET", f"{BASE_URL}/api/ride/reservations/", headers=auth_header(pass2_access))
# #         reservas_pass2 = check_response(resp, 200)
# #         if reservas_pass2 and len(reservas_pass2) > 0:
# #             reserva_cancelar = reservas_pass2[0]["id"]
# #             print(f"\n🧪 Teste de cancelamento (deve incrementar warning_count)...")
# #             resp = req("PATCH", f"{BASE_URL}/api/ride/reservations/{reserva_cancelar}/", json={"status": "cancelada"}, headers=auth_header(pass2_access))
# #             if resp.status_code == 200:
# #                 print("✅ Reserva cancelada com sucesso")
# #                 print("⚠️ Para testar suspensão, seriam necessários mais cancelamentos. Pulando.")
# #             else:
# #                 print(f"⚠️ Falha ao cancelar reserva: {resp.status_code}")

# # # ------------------------------------------------------------
# # # 12. Autenticação
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("12. TESTES DE AUTENTICAÇÃO (ROTAS PROTEGIDAS)")
# # print("="*60)

# # print("\n🧪 Tentar acessar /api/ride/rides/ sem token (deve retornar 401)...")
# # resp = req("GET", f"{BASE_URL}/api/ride/rides/")
# # if resp.status_code == 401:
# #     print("✅ Acesso negado (401) - correto")
# # else:
# #     print(f"⚠️ Esperado 401, obtido {resp.status_code}")

# # print("\n🧪 Tentar acessar /api/notifications/ sem token (deve retornar 401)...")
# # resp = req("GET", f"{BASE_URL}/api/notifications/")
# # if resp.status_code == 401:
# #     print("✅ Acesso negado (401) - correto")
# # else:
# #     print(f"⚠️ Esperado 401, obtido {resp.status_code}")

# # # ------------------------------------------------------------
# # # 13. Redefinição de senha (ajustado para lidar com 401)
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("13. REDEFINIÇÃO DE SENHA")
# # print("="*60)

# # print("\n📧 Solicitando redefinição de senha para o motorista...")
# # resp = req("POST", f"{BASE_URL}/api/reset-password", json={"email": driver_email})
# # if resp.status_code == 201:
# #     print("✅ Solicitação de redefinição enviada (email deve ser disparado)")
# #     print("\n🧪 Testar validação de token inválido (GET /reset-password?token=invalido)...")
# #     resp = req("GET", f"{BASE_URL}/api/reset-password?token=token_invalido")
# #     if resp.status_code == 404:
# #         print("✅ Token inválido rejeitado (404) - correto")
# #     else:
# #         print(f"⚠️ Esperado 404, obtido {resp.status_code}")
# # elif resp.status_code == 401:
# #     print("⚠️ Rota de redefinição está protegida (401) – pode ser configuração do backend. Ignorando.")
# # else:
# #     print(f"⚠️ Falha ao solicitar redefinição: {resp.status_code}")

# # # ------------------------------------------------------------
# # # 14. Limpeza
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("14. LIMPEZA FINAL")
# # print("="*60)

# # print(f"\n🗑️ Deletando reserva {reservation1_id}...")
# # resp = req("DELETE", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", headers=auth_header(passenger_access))
# # if resp.status_code == 204:
# #     print("✅ Reserva deletada")
# # else:
# #     print(f"⚠️ DELETE reserva retornou {resp.status_code}")

# # print(f"\n🗑️ Deletando carona 2 (ID {ride2_id})...")
# # resp = req("DELETE", f"{BASE_URL}/api/ride/rides/{ride2_id}/", headers=auth_header(new_driver_access))
# # if resp.status_code == 204:
# #     print("✅ Carona 2 deletada")
# # else:
# #     print(f"⚠️ DELETE carona retornou {resp.status_code}")

# # # ------------------------------------------------------------
# # # 15. Logout
# # # ------------------------------------------------------------
# # print("\n" + "="*60)
# # print("15. LOGOUT")
# # print("="*60)

# # print("\n🚪 Logout (POST /api/logout/)...")
# # logout_refresh = new_driver_refresh if new_driver_refresh else driver_refresh
# # resp = req("POST", f"{BASE_URL}/api/logout/", json={"refresh": logout_refresh}, headers=auth_header(new_driver_access))
# # if resp.status_code == 205:
# #     print("✅ Logout realizado")
# # else:
# #     print(f"⚠️ Logout retornou {resp.status_code}")

# # print("\n" + "="*60)
# # print("🎉 TESTES CONCLUÍDOS COM SUCESSO (OU COM AVISOS)")
# # print("="*60)

# import requests
# import uuid
# import random
# import time
# import json
# from datetime import datetime, timedelta, timezone

# BASE_URL = "http://localhost:8000"

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
#     resp = requests.post(f"{BASE_URL}/api/login/", json={"email": email, "password": password})
#     data = check_response(resp)
#     return data["access"], data["refresh"]

# def auth_header(token):
#     return {"Authorization": f"Bearer {token}"}

# # Função de requisição com log detalhado e formatação
# def req(method, url, **kwargs):
#     headers = kwargs.get("headers")
#     # Mascarar token no log se presente
#     masked_headers = None
#     if headers and "Authorization" in headers:
#         token = headers["Authorization"].split()[1]
#         masked = token[:10] + "..." + token[-10:] if len(token) > 20 else token
#         masked_headers = {"Authorization": f"Bearer {masked}"}
#     else:
#         masked_headers = headers

#     # Prepara o corpo para exibição formatada
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

# print("\n⏳ Aguardando sincronização Kafka (5s)...")
# time.sleep(3)

# # ------------------------------------------------------------
# # 2. Login
# # ------------------------------------------------------------
# print("\n🔐 Fazendo login...")
# driver_access, driver_refresh = get_tokens(driver_email, password)
# passenger_access, passenger_refresh = get_tokens(passenger_email, password)
# print("✅ Tokens obtidos")

# # ------------------------------------------------------------
# # 3. Profile e refresh
# # ------------------------------------------------------------
# print("\n✏️ Atualizando perfil (PATCH /api/profile/)...")
# resp = req("PATCH", f"{BASE_URL}/api/profile/", data={"telefone": "11999999999"}, headers=auth_header(driver_access))
# check_response(resp, 200)

# print("\n🔄 Refresh token (POST /api/token/refresh/)...")
# resp = req("POST", f"{BASE_URL}/api/token/refresh/", json={"refresh": driver_refresh})
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
#     "plate": "ABC1D23", "seats": 5,
#     "type_vehicle": "carro" 
# }
# resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle_data, headers=auth_header(new_driver_access))
# vehicle1 = check_response(resp, 201)
# vehicle1_id = vehicle1["id"]
# print(f"✅ Veículo 1 criado:\n{json.dumps(vehicle1, indent=2)}")

# print("\n🚗 Criando veículo 2...")
# vehicle2_data = {
#     "user": driver_data["id"], "model": "Ford Ka", "color": "azul",
#     "plate": "XYZ9A87", "seats": 4,
#     "type_vehicle": "carro" 
# }
# resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle2_data, headers=auth_header(new_driver_access))
# vehicle2 = check_response(resp, 201)
# vehicle2_id = vehicle2["id"]
# print(f"✅ Veículo 2 criado:\n{json.dumps(vehicle2, indent=2)}")

# # ------------------------------------------------------------
# # 5. Testar endpoints de veículos
# # ------------------------------------------------------------
# print("\n📋 Listando veículos (GET)...")
# resp = req("GET", f"{BASE_URL}/api/ride/vehicles/", headers=auth_header(new_driver_access))
# veiculos = check_response(resp, 200)
# print(f"✅ Veículos encontrados: {len(veiculos)}\n{json.dumps(veiculos, indent=2)}")

# print(f"\n🔍 Detalhe veículo {vehicle1_id} (GET)...")
# resp = req("GET", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", headers=auth_header(new_driver_access))
# veiculo_detalhe = check_response(resp, 200)
# print(f"✅ Detalhe:\n{json.dumps(veiculo_detalhe, indent=2)}")

# print(f"\n✏️ Atualizar veículo {vehicle1_id} (PATCH)...")
# resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", json={"color": "verde"}, headers=auth_header(new_driver_access))
# veiculo_atualizado = check_response(resp, 200)
# print(f"✅ Veículo atualizado:\n{json.dumps(veiculo_atualizado, indent=2)}")

# print(f"\n🗑️ Deletar veículo {vehicle2_id} (DELETE)...")
# resp = req("DELETE", f"{BASE_URL}/api/ride/vehicles/{vehicle2_id}/", headers=auth_header(new_driver_access))
# if resp.status_code == 204:
#     print("✅ Veículo 2 deletado")
# else:
#     print(f"⚠️ DELETE retornou {resp.status_code}")

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
# resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride_data, headers=auth_header(new_driver_access))
# ride1 = check_response(resp, 201)
# ride1_id = ride1["id"]
# ride1_uuid = ride1["uuid"]
# print(f"✅ Carona 1 criada:\n{json.dumps(ride1, indent=2)}")

# print("\n🚕 Criando carona 2...")
# ride2_data = {
#     "vehicle": vehicle1_id, "origin": "Centro", "destination": "Shopping",
#     "start_time": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
#     "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
#     "available_seats": 2, "status": "pendente", "price": 20.00
# }
# resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride2_data, headers=auth_header(new_driver_access))
# ride2 = check_response(resp, 201)
# ride2_id = ride2["id"]
# print(f"✅ Carona 2 criada:\n{json.dumps(ride2, indent=2)}")

# # ------------------------------------------------------------
# # 7. Testar endpoints de rides
# # ------------------------------------------------------------
# print("\n📋 Listando caronas (GET)...")
# resp = req("GET", f"{BASE_URL}/api/ride/rides/", headers=auth_header(new_driver_access))
# caronas = check_response(resp, 200)
# print(f"✅ Caronas encontradas: {len(caronas)}\n{json.dumps(caronas, indent=2)}")

# print(f"\n🔍 Detalhe carona {ride1_id} (GET)...")
# resp = req("GET", f"{BASE_URL}/api/ride/rides/{ride1_id}/", headers=auth_header(new_driver_access))
# carona_detalhe = check_response(resp, 200)
# print(f"✅ Detalhe:\n{json.dumps(carona_detalhe, indent=2)}")

# print(f"\n✏️ Atualizar carona {ride1_id} (PATCH)...")
# patch_ride = {
#     "vehicle": vehicle1_id, "origin": "Terminal Central", "destination": "centro",
#     "start_time": start_time, "expected_arrival": expected_arrival,
#     "available_seats": 3, "status": "pendente", "price": "45.00"
# }
# resp = req("PATCH", f"{BASE_URL}/api/ride/rides/{ride1_id}/", json=patch_ride, headers=auth_header(new_driver_access))
# carona_atualizada = check_response(resp, 200)
# print(f"✅ Carona atualizada:\n{json.dumps(carona_atualizada, indent=2)}")

# # ------------------------------------------------------------
# # 8. Reservas
# # ------------------------------------------------------------
# print("\n📅 Criando reserva...")
# reservation_data = {
#     "ride": ride1_id, "passenger": passenger_data["id"],
#     "requested_seats": 2, "status": "pendente"
# }
# resp = req("POST", f"{BASE_URL}/api/ride/reservations/", json=reservation_data, headers=auth_header(passenger_access))
# reservation1 = check_response(resp, 201)
# reservation1_id = reservation1["id"]
# print(f"✅ Reserva criada:\n{json.dumps(reservation1, indent=2)}")

# print("\n📋 Listando reservas (GET)...")
# resp = req("GET", f"{BASE_URL}/api/ride/reservations/", headers=auth_header(passenger_access))
# reservas = check_response(resp, 200)
# print(f"✅ Reservas encontradas: {len(reservas)}\n{json.dumps(reservas, indent=2)}")

# print(f"\n🔍 Detalhe reserva {reservation1_id} (GET)...")
# resp = req("GET", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", headers=auth_header(passenger_access))
# reserva_detalhe = check_response(resp, 200)
# print(f"✅ Detalhe:\n{json.dumps(reserva_detalhe, indent=2)}")

# print(f"\n✏️ Confirmar reserva {reservation1_id} (PATCH)...")
# resp = req("PATCH", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", json={"status": "confirmada"}, headers=auth_header(passenger_access))
# reserva_confirmada = check_response(resp, 200)
# print(f"✅ Reserva confirmada:\n{json.dumps(reserva_confirmada, indent=2)}")

# # ------------------------------------------------------------
# # 9. Chat - corrigido: verifica se sala já existe
# # ------------------------------------------------------------
# print("\n💬 Chat: obtendo ou criando sala...")
# time.sleep(3)

# # Tenta obter a sala primeiro
# resp_get = req("GET", f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/", headers=auth_header(passenger_access))
# if resp_get.status_code == 200:
#     room = resp_get.json()
#     print(f"✅ Sala já existente: {json.dumps(room, indent=2)}")
# else:
#     # Sala não existe, criar
#     resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", json={"carona_id": ride1_uuid}, headers=auth_header(passenger_access))
#     if resp_post.status_code in (200, 201):
#         room = resp_post.json()
#         print(f"✅ Sala criada: {json.dumps(room, indent=2)}")
#     else:
#         print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
#         room = None

# if room:
#     msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
#     print("\n💬 Enviando mensagem do passageiro...")
#     resp = req("POST", msg_url, json={"usuario_id": passenger_data["id"], "conteudo": "Olá, motorista! Estou no ponto."}, headers=auth_header(passenger_access))
#     msg_pass = check_response(resp, 201)
#     print(f"✅ Mensagem enviada:\n{json.dumps(msg_pass, indent=2)}")

#     print("\n💬 Enviando mensagem do motorista...")
#     resp = req("POST", msg_url, json={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
#     msg_motorista = check_response(resp, 201)
#     print(f"✅ Mensagem enviada:\n{json.dumps(msg_motorista, indent=2)}")

#     print("\n📜 Obtendo histórico de mensagens...")
#     resp = req("GET", msg_url, headers=auth_header(passenger_access))
#     messages = check_response(resp, 200)
#     print(f"✅ {len(messages)} mensagens trocadas:\n{json.dumps(messages, indent=2)}")
# else:
#     print("⚠️ Pulando chat devido a erro na criação/obtenção da sala")

# # ------------------------------------------------------------
# # 10. Deletes finais
# # ------------------------------------------------------------
# print(f"\n🗑️ Deletando reserva {reservation1_id}...")
# resp = req("DELETE", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", headers=auth_header(passenger_access))
# if resp.status_code == 204:
#     print("✅ Reserva deletada")
# else:
#     print(f"⚠️ DELETE reserva retornou {resp.status_code}")

# print(f"\n🗑️ Deletando carona 2 (ID {ride2_id})...")
# resp = req("DELETE", f"{BASE_URL}/api/ride/rides/{ride2_id}/", headers=auth_header(new_driver_access))
# if resp.status_code == 204:
#     print("✅ Carona 2 deletada")
# else:
#     print(f"⚠️ DELETE carona retornou {resp.status_code}")

# # ------------------------------------------------------------
# # 11. Logout
# # ------------------------------------------------------------
# print("\n🚪 Logout (POST /api/logout/)...")
# logout_refresh = new_driver_refresh if new_driver_refresh else driver_refresh
# resp = req("POST", f"{BASE_URL}/api/logout/", json={"refresh": logout_refresh}, headers=auth_header(new_driver_access))
# if resp.status_code == 205:
#     print("✅ Logout realizado")
# else:
#     print(f"⚠️ Logout retornou {resp.status_code}")

# print("\n🎉 Testes concluídos com logs detalhados e formatados!")

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
    resp = requests.post(f"{BASE_URL}/api/login/", json={"email": email, "password": password})
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
time.sleep(3)

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
resp = req("POST", f"{BASE_URL}/api/token/refresh/", json={"refresh": driver_refresh})
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
resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle_data, headers=auth_header(new_driver_access))
vehicle1 = check_response(resp, 201)
vehicle1_id = vehicle1["id"]
print(f"✅ Veículo 1 criado:\n{json.dumps(vehicle1, indent=2)}")

print("\n🚗 Criando veículo 2...")
vehicle2_data = {
    "user": driver_data["id"], "model": "Ford Ka", "color": "azul",
    "plate": "XYZ9A87", "seats": 4,
    "type_vehicle": "carro" 
}
resp = req("POST", f"{BASE_URL}/api/ride/vehicles/", json=vehicle2_data, headers=auth_header(new_driver_access))
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
# resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", json={"color": "Vermelho"}, headers=auth_header(new_driver_access))
resp = req("PATCH", f"{BASE_URL}/api/ride/vehicles/{vehicle1_id}/", json={"color": "azul"}, headers=auth_header(new_driver_access))
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
resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride_data, headers=auth_header(new_driver_access))
ride1 = check_response(resp, 201)
ride1_id = ride1["id"]
ride1_uuid = ride1["uuid"]
print(f"✅ Carona 1 criada:\n{json.dumps(ride1, indent=2)}")

print("\n🚕 Criando carona 2...")
ride2_data = {
    "vehicle": vehicle1_id, "origin": "Centro", "destination": "Shopping",
    "start_time": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
    "expected_arrival": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    "available_seats": 2, "status": "pendente", "price": 20.00
}
resp = req("POST", f"{BASE_URL}/api/ride/rides/", json=ride2_data, headers=auth_header(new_driver_access))
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
resp = req("PATCH", f"{BASE_URL}/api/ride/rides/{ride1_id}/", json=patch_ride, headers=auth_header(new_driver_access))
carona_atualizada = check_response(resp, 200)
print(f"✅ Carona atualizada:\n{json.dumps(carona_atualizada, indent=2)}")

# ------------------------------------------------------------
# 8. Reservas
# ------------------------------------------------------------
print("\n📅 Criando reserva...")
reservation_data = {
    "ride": ride1_id, "passenger": passenger_data["id"],
    "requested_seats": 2, "status": "pendente"
}
resp = req("POST", f"{BASE_URL}/api/ride/reservations/", json=reservation_data, headers=auth_header(passenger_access))
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
resp = req("PATCH", f"{BASE_URL}/api/ride/reservations/{reservation1_id}/", json={"status": "confirmada"}, headers=auth_header(passenger_access))
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
    resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", json=chat_payload, headers=auth_header(passenger_access))
    if resp_post.status_code in (200, 201):
        room = resp_post.json()
        print(f"✅ Sala criada com participantes:\n{json.dumps(room, indent=2)}")
    else:
        print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
        room = None

if room:
    msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
    print("\n💬 Enviando mensagem do passageiro...")
    resp = req("POST", msg_url, json={"usuario_id": passenger_data["id"], "conteudo": "Olá, motorista! Estou no ponto."}, headers=auth_header(passenger_access))
    msg_pass = check_response(resp, 201)
    print(f"✅ Mensagem enviada:\n{json.dumps(msg_pass, indent=2)}")

    print("\n💬 Enviando mensagem do motorista...")
    resp = req("POST", msg_url, json={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
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
    resp_post = req("POST", f"{BASE_URL}/api/chat/rooms/", json=chat_payload, headers=auth_header(passenger_access))
    if resp_post.status_code in (200, 201):
        room = resp_post.json()
        print(f"✅ Sala criada com participantes:\n{json.dumps(room, indent=2)}")
    else:
        print(f"❌ Erro ao criar sala: {resp_post.status_code} - {resp_post.text}")
        room = None

if room:
    msg_url = f"{BASE_URL}/api/chat/rooms/{ride1_uuid}/messages/"
    print("\n💬 Enviando mensagem do motorista...")
    resp = req("POST", msg_url, json={"usuario_id": driver_data["id"], "conteudo": "Chego em 5 minutos."}, headers=auth_header(new_driver_access))
    msg_motorista = check_response(resp, 201)
    if msg_motorista is not None:
        print(f"✅ Mensagem do motorista enviada:\n{json.dumps(msg_motorista, indent=2)}")
    else:
        print("⚠️ Falha ao enviar mensagem do motorista")

    print("\n💬 Enviando mensagem do passageiro...")
    resp = req("POST", msg_url, json={"usuario_id": passenger_data["id"], "conteudo": "Olá, estou no ponto!"}, headers=auth_header(passenger_access))
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
resp = req("POST", f"{BASE_URL}/api/logout/", json={"refresh": logout_refresh}, headers=auth_header(new_driver_access))
if resp.status_code == 205:
    print("✅ Logout realizado")
else:
    print(f"⚠️ Logout retornou {resp.status_code}")

print("\n🎉 Testes concluídos com logs detalhados e formatados!")