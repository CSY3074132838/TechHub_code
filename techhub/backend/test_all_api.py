# -*- coding: utf-8 -*-
from app import create_app

app = create_app()
client = app.test_client()

# Login
r = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
token = r.get_json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

def test_api(method, url, data=None, expect=200):
    if method == 'GET':
        r = client.get(url, headers=headers)
    elif method == 'POST':
        r = client.post(url, json=data, headers=headers)
    elif method == 'PUT':
        r = client.put(url, json=data, headers=headers)
    elif method == 'DELETE':
        r = client.delete(url, headers=headers)
    status = 'OK' if r.status_code == expect else f'FAIL({r.status_code})'
    if r.status_code != expect:
        print(f'  Response: {r.get_json()}')
    return status

# Auth APIs
print('=== Auth ===')
print('GET /api/auth/me:', test_api('GET', '/api/auth/me'))

# Dashboard APIs
print('\n=== Dashboard ===')
print('GET /api/dashboard/overview:', test_api('GET', '/api/dashboard/overview'))
print('GET /api/dashboard/statistics:', test_api('GET', '/api/dashboard/statistics'))
print('GET /api/dashboard/crm-overview:', test_api('GET', '/api/dashboard/crm-overview'))
print('GET /api/dashboard/crm-ranking:', test_api('GET', '/api/dashboard/crm-ranking'))

# Project APIs
print('\n=== Projects ===')
print('GET /api/projects/:', test_api('GET', '/api/projects/'))
print('POST /api/projects/:', test_api('POST', '/api/projects/', {'name': 'Test Project', 'client_id': 1}))

# Client APIs
print('\n=== Clients ===')
print('GET /api/clients/:', test_api('GET', '/api/clients/'))
print('GET /api/clients/stats:', test_api('GET', '/api/clients/stats'))
print('GET /api/clients/options:', test_api('GET', '/api/clients/options'))
print('POST /api/clients/:', test_api('POST', '/api/clients/', {'name': 'New Client', 'status': 'potential'}))

# Contract APIs
print('\n=== Contracts ===')
print('GET /api/contracts/:', test_api('GET', '/api/contracts/'))

# Ticket APIs
print('\n=== Tickets ===')
print('GET /api/tickets/:', test_api('GET', '/api/tickets/'))
print('GET /api/tickets/stats:', test_api('GET', '/api/tickets/stats'))

# Approval APIs
print('\n=== Approvals ===')
print('GET /api/approvals/pending-count:', test_api('GET', '/api/approvals/pending-count'))

print('\n=== Done ===')
