"""Mock server for D365 F&O integration testing.

This module provides a mock HTTP server that simulates D365 F&O OData API responses.
It's designed to be fast, reliable, and provide realistic responses for testing.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from aiohttp import web
from aiohttp.web import Request, Response, Application
import logging

logger = logging.getLogger(__name__)

class D365MockServer:
    """Mock server that simulates D365 F&O OData API endpoints."""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.app: Optional[Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Mock data stores
        self.entities_data: Dict[str, List[Dict[str, Any]]] = {
            'Customers': [
                {
                    'CustomerAccount': 'US-001',
                    'CustomerName': 'Contoso Corporation',
                    'CustomerGroupId': 'CORPORATE',
                    'CurrencyCode': 'USD',
                    'PaymentTerms': 'Net30'
                },
                {
                    'CustomerAccount': 'US-002', 
                    'CustomerName': 'Fabrikam Inc',
                    'CustomerGroupId': 'CORPORATE',
                    'CurrencyCode': 'USD',
                    'PaymentTerms': 'Net15'
                }
            ],
            'Vendors': [
                {
                    'VendorAccount': 'V-001',
                    'VendorName': 'Fourth Coffee',
                    'VendorGroupId': 'SERVICES',
                    'CurrencyCode': 'USD',
                    'PaymentTerms': 'Net30'
                }
            ],
            'DataManagementEntities': []
        }
        
        # Version information
        self.version_info = {
            'application': '10.0.1985.137',
            'platform': '10.0.1985.137',
            'application_build': '10.0.1985.137'
        }
        
        # Metadata responses
        self.metadata_responses = {
            'DataEntities': [
                {
                    'Name': 'Customers',
                    'EntitySetName': 'Customers',
                    'IsReadOnly': False,
                    'LabelId': '@SYS1234',
                    'EntityCategory': 'Master',
                    'DataServiceEnabled': True,
                    'DataManagementEnabled': True
                },
                {
                    'Name': 'Vendors',
                    'EntitySetName': 'Vendors', 
                    'IsReadOnly': False,
                    'LabelId': '@SYS5678',
                    'EntityCategory': 'Master',
                    'DataServiceEnabled': True,
                    'DataManagementEnabled': True
                }
            ],
            'PublicEntities': [
                {
                    'Name': 'Customers',
                    'EntitySetName': 'Customers',
                    'IsReadOnly': False,
                    'LabelId': '@SYS1234',
                    'ConfigurationEnabled': True,
                    'Properties': [
                        {
                            'Name': 'CustomerAccount',
                            'TypeName': 'String',
                            'LabelId': '@SYS1001',
                            'IsKey': True,
                            'IsMandatory': True,
                            'AllowEdit': True
                        },
                        {
                            'Name': 'CustomerName',
                            'TypeName': 'String', 
                            'LabelId': '@SYS1002',
                            'IsKey': False,
                            'IsMandatory': True,
                            'AllowEdit': True
                        }
                    ]
                }
            ],
            'PublicEnumerations': [
                {
                    'Name': 'CustVendAccountType',
                    'LabelId': '@SYS9001',
                    'Members': [
                        {
                            'Name': 'Customer',
                            'Value': 0,
                            'LabelId': '@SYS9002'
                        },
                        {
                            'Name': 'Vendor',
                            'Value': 1,
                            'LabelId': '@SYS9003'
                        }
                    ]
                }
            ]
        }
        
        # Label data
        self.labels = {
            '@SYS1234': 'Customers',
            '@SYS5678': 'Vendors',
            '@SYS1001': 'Customer Account',
            '@SYS1002': 'Customer Name',
            '@SYS9001': 'Customer/Vendor Account Type',
            '@SYS9002': 'Customer',
            '@SYS9003': 'Vendor'
        }

    async def setup_routes(self):
        """Setup mock API routes."""
        self.app = web.Application()
        
        # OData endpoints
        self.app.router.add_get('/data', self.handle_data_root)
        self.app.router.add_get('/data/$metadata', self.handle_metadata)
        # Add entity by key routes BEFORE entity collection to ensure proper matching
        self.app.router.add_get('/data/{entity}({key})', self.handle_entity_by_key)
        self.app.router.add_patch('/data/{entity}({key})', self.handle_entity_update)
        self.app.router.add_put('/data/{entity}({key})', self.handle_entity_update)
        self.app.router.add_delete('/data/{entity}({key})', self.handle_entity_delete)
        # Entity collection route must come AFTER entity by key to avoid conflicts
        self.app.router.add_get('/data/{entity}', self.handle_entity_collection)
        self.app.router.add_post('/data/{entity}', self.handle_entity_create)
        
        # Action endpoints
        self.app.router.add_post('/data/{entity}/Microsoft.Dynamics.DataEntities.{action}', self.handle_bound_action)
        self.app.router.add_post('/data/Microsoft.Dynamics.DataEntities.{action}', self.handle_unbound_action)
        
        # Metadata API endpoints
        self.app.router.add_get('/Metadata/DataEntities', self.handle_metadata_data_entities)
        self.app.router.add_get('/Metadata/DataEntities({entity_name})', self.handle_metadata_data_entity)
        self.app.router.add_get('/Metadata/PublicEntities', self.handle_metadata_public_entities)
        self.app.router.add_get('/Metadata/PublicEntities({entity_name})', self.handle_metadata_public_entity)
        self.app.router.add_get('/Metadata/PublicEnumerations', self.handle_metadata_public_enumerations)
        self.app.router.add_get('/Metadata/PublicEnumerations({enum_name})', self.handle_metadata_public_enumeration)
        
        # Label endpoints
        self.app.router.add_get('/Metadata/Labels', self.handle_labels)
        # Add specific label lookup endpoints
        self.app.router.add_get('/Metadata/Labels(Id={label_id},Language={language})', self.handle_label_by_id)

    async def start(self):
        """Start the mock server."""
        await self.setup_routes()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', self.port)
        await self.site.start()
        logger.info(f"Mock D365 F&O server started on http://localhost:{self.port}")

    async def stop(self):
        """Stop the mock server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Mock D365 F&O server stopped")

    # Route handlers
    
    async def handle_data_root(self, request: Request) -> Response:
        """Handle GET /data - root OData service document."""
        return web.json_response({
            '@odata.context': f'http://localhost:{self.port}/data/$metadata',
            'value': [
                {'name': 'Customers', 'kind': 'EntitySet', 'url': 'Customers'},
                {'name': 'Vendors', 'kind': 'EntitySet', 'url': 'Vendors'},
                {'name': 'DataManagementEntities', 'kind': 'EntitySet', 'url': 'DataManagementEntities'}
            ]
        })
    
    async def handle_metadata(self, request: Request) -> Response:
        """Handle GET /data/$metadata - OData metadata document."""
        metadata_xml = '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="Microsoft.Dynamics.DataEntities" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityContainer Name="Container">
        <EntitySet Name="Customers" EntityType="Microsoft.Dynamics.DataEntities.Customer"/>
        <EntitySet Name="Vendors" EntityType="Microsoft.Dynamics.DataEntities.Vendor"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
        return web.Response(text=metadata_xml, content_type='application/xml')
    
    async def handle_entity_collection(self, request: Request) -> Response:
        """Handle GET /data/{entity} - get entity collection."""
        entity = request.match_info['entity']
        
        if entity not in self.entities_data:
            return web.json_response({'error': {'message': f'Entity set {entity} not found'}}, status=404)
        
        # Handle OData query parameters
        query_params = request.query
        entities = self.entities_data[entity].copy()
        
        # Apply $top
        if '$top' in query_params:
            try:
                top = int(query_params['$top'])
                entities = entities[:top]
            except ValueError:
                pass
        
        # Apply $skip
        if '$skip' in query_params:
            try:
                skip = int(query_params['$skip'])
                entities = entities[skip:]
            except ValueError:
                pass
        
        # Apply $filter (basic implementation)
        if '$filter' in query_params:
            filter_expr = query_params['$filter']
            # Simple contains filter
            if 'contains' in filter_expr.lower():
                # Extract field and value (basic parsing)
                entities = [e for e in entities if any(
                    str(v).lower().find('test') >= 0 for v in e.values()
                )]
        
        return web.json_response({
            '@odata.context': f'http://localhost:{self.port}/data/$metadata#{entity}',
            'value': entities
        })
    
    async def handle_entity_by_key(self, request: Request) -> Response:
        """Handle GET /data/{entity}({key}) - get single entity."""
        entity = request.match_info['entity']
        key = request.match_info['key'].strip("'")
        
        if entity not in self.entities_data:
            return web.json_response({'error': {'message': f'Entity set {entity} not found'}}, status=404)
        
        # Find entity by key (assume first field is key)
        for item in self.entities_data[entity]:
            if str(list(item.values())[0]) == key:
                return web.json_response({
                    '@odata.context': f'http://localhost:{self.port}/data/$metadata#{entity}/$entity',
                    **item
                })
        
        return web.json_response({'error': {'message': f'Entity with key {key} not found'}}, status=404)
    
    async def handle_entity_create(self, request: Request) -> Response:
        """Handle POST /data/{entity} - create entity."""
        entity = request.match_info['entity']
        
        if entity not in self.entities_data:
            return web.json_response({'error': {'message': f'Entity set {entity} not found'}}, status=404)
        
        try:
            data = await request.json()
            # Add timestamp and generate ID if needed
            if 'CreatedDateTime' not in data:
                data['CreatedDateTime'] = datetime.now(timezone.utc).isoformat() + 'Z'
            
            self.entities_data[entity].append(data)
            
            return web.json_response({
                '@odata.context': f'http://localhost:{self.port}/data/$metadata#{entity}/$entity',
                **data
            }, status=201)
        except Exception as e:
            return web.json_response({'error': {'message': str(e)}}, status=400)
    
    async def handle_entity_update(self, request: Request) -> Response:
        """Handle PATCH/PUT /data/{entity}({key}) - update entity."""
        entity = request.match_info['entity']
        key = request.match_info['key'].strip("'")
        
        if entity not in self.entities_data:
            return web.json_response({'error': {'message': f'Entity set {entity} not found'}}, status=404)
        
        try:
            data = await request.json()
            
            # Find and update entity
            for i, item in enumerate(self.entities_data[entity]):
                if str(list(item.values())[0]) == key:
                    if request.method == 'PATCH':
                        self.entities_data[entity][i].update(data)
                    else:  # PUT
                        self.entities_data[entity][i] = data
                    
                    return web.json_response({
                        '@odata.context': f'http://localhost:{self.port}/data/$metadata#{entity}/$entity',
                        **self.entities_data[entity][i]
                    })
            
            return web.json_response({'error': {'message': f'Entity with key {key} not found'}}, status=404)
        except Exception as e:
            return web.json_response({'error': {'message': str(e)}}, status=400)
    
    async def handle_entity_delete(self, request: Request) -> Response:
        """Handle DELETE /data/{entity}({key}) - delete entity."""
        entity = request.match_info['entity']
        key = request.match_info['key'].strip("'")
        
        if entity not in self.entities_data:
            return web.json_response({'error': {'message': f'Entity set {entity} not found'}}, status=404)
        
        # Find and delete entity
        for i, item in enumerate(self.entities_data[entity]):
            if str(list(item.values())[0]) == key:
                del self.entities_data[entity][i]
                return web.Response(status=204)
        
        return web.json_response({'error': {'message': f'Entity with key {key} not found'}}, status=404)
    
    async def handle_bound_action(self, request: Request) -> Response:
        """Handle bound action calls."""
        entity = request.match_info['entity']
        action = request.match_info['action']
        
        # Mock version methods for DataManagementEntities
        if entity == 'DataManagementEntities':
            if action == 'GetApplicationVersion':
                return web.json_response({'value': self.version_info['application']})
            elif action == 'GetPlatformBuildVersion':
                return web.json_response({'value': self.version_info['platform']})
            elif action == 'GetApplicationBuildVersion':
                return web.json_response({'value': self.version_info['application_build']})
        
        return web.json_response({'error': {'message': f'Action {action} not found for entity {entity}'}}, status=404)
    
    async def handle_unbound_action(self, request: Request) -> Response:
        """Handle unbound action calls."""
        action = request.match_info['action']
        return web.json_response({'error': {'message': f'Unbound action {action} not found'}}, status=404)
    
    # Metadata API handlers
    
    async def handle_metadata_data_entities(self, request: Request) -> Response:
        """Handle GET /Metadata/DataEntities."""
        entities = self.metadata_responses['DataEntities'].copy()
        
        # Apply query parameters
        query_params = request.query
        if '$top' in query_params:
            try:
                top = int(query_params['$top'])
                entities = entities[:top]
            except ValueError:
                pass
        
        return web.json_response({
            '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#DataEntities',
            'value': entities
        })
    
    async def handle_metadata_data_entity(self, request: Request) -> Response:
        """Handle GET /Metadata/DataEntities({entity_name})."""
        entity_name = request.match_info['entity_name'].strip("'")
        
        for entity in self.metadata_responses['DataEntities']:
            if entity['Name'] == entity_name:
                return web.json_response({
                    '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#DataEntities/$entity',
                    **entity
                })
        
        return web.json_response({'error': {'message': f'DataEntity {entity_name} not found'}}, status=404)
    
    async def handle_metadata_public_entities(self, request: Request) -> Response:
        """Handle GET /Metadata/PublicEntities."""
        entities = self.metadata_responses['PublicEntities'].copy()
        
        # Apply query parameters
        query_params = request.query
        if '$top' in query_params:
            try:
                top = int(query_params['$top'])
                entities = entities[:top]
            except ValueError:
                pass
        
        return web.json_response({
            '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#PublicEntities',
            'value': entities
        })
    
    async def handle_metadata_public_entity(self, request: Request) -> Response:
        """Handle GET /Metadata/PublicEntities({entity_name})."""
        entity_name = request.match_info['entity_name'].strip("'")
        
        for entity in self.metadata_responses['PublicEntities']:
            if entity['Name'] == entity_name:
                return web.json_response({
                    '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#PublicEntities/$entity',
                    **entity
                })
        
        return web.json_response({'error': {'message': f'PublicEntity {entity_name} not found'}}, status=404)
    
    async def handle_metadata_public_enumerations(self, request: Request) -> Response:
        """Handle GET /Metadata/PublicEnumerations."""
        enums = self.metadata_responses['PublicEnumerations'].copy()
        
        # Apply query parameters
        query_params = request.query
        if '$top' in query_params:
            try:
                top = int(query_params['$top'])
                enums = enums[:top]
            except ValueError:
                pass
        
        return web.json_response({
            '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#PublicEnumerations',
            'value': enums
        })
    
    async def handle_metadata_public_enumeration(self, request: Request) -> Response:
        """Handle GET /Metadata/PublicEnumerations({enum_name})."""
        enum_name = request.match_info['enum_name'].strip("'")
        
        for enum in self.metadata_responses['PublicEnumerations']:
            if enum['Name'] == enum_name:
                return web.json_response({
                    '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#PublicEnumerations/$entity',
                    **enum
                })
        
        return web.json_response({'error': {'message': f'PublicEnumeration {enum_name} not found'}}, status=404)
    
    async def handle_labels(self, request: Request) -> Response:
        """Handle GET /Metadata/Labels - get label text."""
        query_params = request.query
        
        # Handle label ID query
        if 'labelId' in query_params:
            label_id = query_params['labelId']
            if label_id in self.labels:
                return web.json_response({
                    'LabelId': label_id,
                    'Text': self.labels[label_id],
                    'Language': query_params.get('language', 'en-US')
                })
            else:
                return web.json_response({'error': {'message': f'Label {label_id} not found'}}, status=404)
        
        # Return all labels
        return web.json_response({
            '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#Labels',
            'value': [
                {'LabelId': lid, 'Text': text, 'Language': 'en-US'}
                for lid, text in self.labels.items()
            ]
        })
    
    async def handle_label_by_id(self, request: Request) -> Response:
        """Handle GET /Metadata/Labels(Id='{label_id}',Language='{language}')."""
        label_id = request.match_info['label_id'].strip("'")
        language = request.match_info['language'].strip("'")
        
        if label_id in self.labels:
            return web.json_response({
                '@odata.context': f'http://localhost:{self.port}/Metadata/$metadata#Labels/$entity',
                'LabelId': label_id,
                'Value': self.labels[label_id],  # Client expects 'Value' not 'Text'
                'Language': language
            })
        else:
            return web.json_response({'error': {'message': f'Label {label_id} not found'}}, status=404)