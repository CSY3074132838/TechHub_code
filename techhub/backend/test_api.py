# -*- coding: utf-8 -*-
from app import create_app

app = create_app()
client = app.test_client()

# Test login
print("=== Testing Login ===")
r = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
print('Login status:', r.status_code)
if r.status_code != 200:
    print('Login failed:', r.get_json())
    exit(1)

token = r.get_json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test create client
print("\n=== Testing Create Client ===")
r = client.post('/api/clients/', json={
    'name': 'Test Client',
    'contact_name': 'John Doe',
    'status': 'potential',
    'level': 'a'
}, headers=headers)
print('Create client status:', r.status_code)
print('Create client response:', r.get_json())

# Test get clients
print("\n=== Testing Get Clients ===")
r = client.get('/api/clients/', headers=headers)
print('Get clients status:', r.status_code)
data = r.get_json()
print('Clients count:', len(data.get('clients', [])))

# Test get client options
print("\n=== Testing Client Options ===")
r = client.get('/api/clients/options', headers=headers)
print('Options status:', r.status_code)
print('Options count:', len(r.get_json().get('clients', [])))

# Test create contract
print("\n=== Testing Create Contract ===")
client_id = data['clients'][0]['id'] if data.get('clients') else 1
r = client.post('/api/contracts/', json={
    'name': 'Test Contract',
    'client_id': client_id,
    'amount': 100000,
    'status': 'draft'
}, headers=headers)
print('Create contract status:', r.status_code)
print('Create contract response:', r.get_json())

# Test get contracts
print("\n=== Testing Get Contracts ===")
r = client.get('/api/contracts/', headers=headers)
print('Get contracts status:', r.status_code)
print('Contracts count:', len(r.get_json().get('contracts', [])))

# Test create ticket
print("\n=== Testing Create Ticket ===")
r = client.post('/api/tickets/', json={
    'title': 'Test Ticket',
    'client_id': client_id,
    'priority': 'high',
    'description': 'This is a test ticket'
}, headers=headers)
print('Create ticket status:', r.status_code)
print('Create ticket response:', r.get_json())

# Test get tickets
print("\n=== Testing Get Tickets ===")
r = client.get('/api/tickets/', headers=headers)
print('Get tickets status:', r.status_code)
print('Tickets count:', len(r.get_json().get('tickets', [])))

# Test CRM dashboard
print("\n=== Testing CRM Dashboard ===")
r = client.get('/dashboard/crm-overview', headers=headers)
print('CRM overview status:', r.status_code)
print('CRM overview:', r.get_json())

r = client.get('/dashboard/crm-ranking', headers=headers)
print('CRM ranking status:', r.status_code)

print("\n=== All tests completed ===")
