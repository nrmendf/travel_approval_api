from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import openai

openai.api_key = "sk-proj-Q2VP4DuGO-xRKCkY146Pmwk7pLz3HfinuSEzRuajK8GaYunYaSP3pGvMfCgRBCWZA0fZ7wXbpmT3BlbkFJindV1-r-ypfpnrPiwbVFjqS3DKjStW8OLdxY_32zFlan5LQ5vFjUetM5oEE0Llzt4KCoCPU2QAENAI"

app = FastAPI()

# Definindo as políticas de viagem
TRAVEL_POLICIES = {
    "max_trip_duration": 15,  # Dias
    "max_budget": 50000.0,    # R$ (Reais)
    "max_ticket_price": 1000.0  # R$ (Preço máximo da passagem)
}

# Modelo para a solicitação de viagem
class TravelRequest(BaseModel):
    employee_name: str
    department: str
    origin: str
    destination: str
    departure_date: str
    return_date: str
    estimated_budget: float

# Modelo para a resposta
class TravelResponse(BaseModel):
    accepted: bool
    violated_policies: list

# Validação das políticas
def validate_policies(request: TravelRequest):
    violated = []

    try:
        # Convertendo datas para datetime
        departure_date = datetime.fromisoformat(request.departure_date)
        return_date = datetime.fromisoformat(request.return_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS).")

    trip_duration = (return_date - departure_date).days

    # Validação de duração da viagem
    if trip_duration > TRAVEL_POLICIES["max_trip_duration"]:
        violated.append(f"Maximum trip duration exceeded ({TRAVEL_POLICIES['max_trip_duration']} days)")

    # Validação do orçamento estimado
    if request.estimated_budget > TRAVEL_POLICIES["max_budget"]:
        violated.append(f"Maximum budget exceeded (R$ {TRAVEL_POLICIES['max_budget']:.2f})")

    return violated

# Chamada ao modelo de linguagem (LLM)
def analyze_with_llm(request: TravelRequest):
    prompt = f"""
    Avalie a seguinte solicitação de viagem:
    - Nome: {request.employee_name}
    - Departamento: {request.department}
    - Origem: {request.origin}
    - Destino: {request.destination}
    - Data de partida: {request.departure_date}
    - Data de retorno: {request.return_date}
    - Orçamento estimado: R$ {request.estimated_budget:.2f}

    Políticas de viagem:
    - Duração máxima: {TRAVEL_POLICIES['max_trip_duration']} dias
    - Orçamento máximo: R$ {TRAVEL_POLICIES['max_budget']:.2f}

    Informe se a viagem é aprovada e liste as políticas violadas.
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    output = response.choices[0].text.strip()

    # Determinando aprovação
    if "não aprovada" in output.lower():
        return {"accepted": False, "violated_policies": [output]}
    return {"accepted": True, "violated_policies": []}

# Endpoint da API
@app.post("/approve_travel", response_model=TravelResponse)
def approve_travel(request: TravelRequest):
    violated_policies = validate_policies(request)

    if violated_policies:
        return TravelResponse(accepted=False, violated_policies=violated_policies)

    llm_response = analyze_with_llm(request)
    return TravelResponse(accepted=llm_response["accepted"], violated_policies=llm_response["violated_policies"])