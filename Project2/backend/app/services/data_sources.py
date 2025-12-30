"""
Schema-Agnostic & Heterogeneous Data Access Layer for Multi-Cloud Cost Optimization

This layer provides:
1. Schema-Agnostic: Handles different data schemas (AWS vs GCP vs Azure formats)
2. Heterogeneous: Supports multiple data source types (files, databases, APIs)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime
from loguru import logger
import httpx


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return schema information for this data source"""
        pass
    
    @abstractmethod
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query the data source with given parameters"""
        pass
    
    @abstractmethod
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate if query is safe and allowed"""
        pass


class CSVDataSource(DataSource):
    """CSV file data source - for mock cloud billing data"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = pd.read_csv(file_path)
        self._schema = None
        logger.info(f"✅ Loaded CSV data source: {file_path} ({len(self.df)} rows)")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get CSV schema"""
        if self._schema is None:
            self._schema = {
                "type": "csv",
                "source": self.file_path,
                "columns": list(self.df.columns),
                "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
                "row_count": len(self.df)
            }
        return self._schema
    
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate query parameters"""
        if 'limit' in query_params and query_params['limit'] > 10000:
            return False
        return True
    
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query CSV data"""
        if not self.validate_query(query_params):
            raise ValueError("Query validation failed")
        
        df_filtered = self.df.copy()
        
        # Apply filters
        if 'filter' in query_params:
            for key, value in query_params['filter'].items():
                if key in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[key] == value]
        
        # Apply date range if provided
        if 'date_from' in query_params and 'date_to' in query_params:
            date_col = query_params.get('date_column', 'date')
            if date_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[date_col] >= query_params['date_from']) &
                    (df_filtered[date_col] <= query_params['date_to'])
                ]
        
        # Apply sorting
        if 'sort' in query_params:
            sort_col = query_params['sort'].get('column')
            ascending = query_params['sort'].get('ascending', True)
            if sort_col and sort_col in df_filtered.columns:
                df_filtered = df_filtered.sort_values(sort_col, ascending=ascending)
        
        # Apply limit
        limit = query_params.get('limit', 100)
        result = df_filtered.head(limit).to_dict('records')
        
        return result


class AWSDataSource(DataSource):
    """AWS Cost and Usage Report data source adapter"""
    
    def __init__(self, billing_file_path: str):
        """
        Initialize AWS data source
        
        Args:
            billing_file_path: Path to AWS billing CSV (Cost and Usage Report format)
        """
        self.file_path = billing_file_path
        self.df = pd.read_csv(billing_file_path)
        self._schema = None
        logger.info(f"✅ Loaded AWS billing data: {billing_file_path} ({len(self.df)} rows)")
    
    def get_schema(self) -> Dict[str, Any]:
        """Discover AWS billing schema"""
        if self._schema is None:
            # Normalize AWS column names to common schema
            aws_columns = {
                'lineItem/UsageStartDate': 'date',
                'lineItem/ProductCode': 'service',
                'lineItem/ResourceId': 'resource_id',
                'lineItem/UnblendedCost': 'cost',
                'lineItem/UsageType': 'usage_type',
                'lineItem/Operation': 'operation',
                'lineItem/AvailabilityZone': 'region',
                'product/InstanceType': 'instance_type',
                'resourceTags/User:Project': 'project'
            }
            
            self._schema = {
                "type": "aws",
                "source": self.file_path,
                "columns": list(self.df.columns),
                "normalized_columns": aws_columns,
                "row_count": len(self.df)
            }
        return self._schema
    
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate query safety"""
        if 'limit' in query_params and query_params['limit'] > 10000:
            return False
        return True
    
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query AWS billing data"""
        if not self.validate_query(query_params):
            raise ValueError("Query validation failed")
        
        df_filtered = self.df.copy()
        
        # Apply filters
        if 'filter' in query_params:
            for key, value in query_params['filter'].items():
                if key in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[key] == value]
        
        # Apply date range
        if 'date_from' in query_params and 'date_to' in query_params:
            date_col = 'lineItem/UsageStartDate'
            if date_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[date_col] >= query_params['date_from']) &
                    (df_filtered[date_col] <= query_params['date_to'])
                ]
        
        limit = query_params.get('limit', 100)
        result = df_filtered.head(limit).to_dict('records')
        
        return result


class GCPDataSource(DataSource):
    """GCP Billing Export data source adapter"""
    
    def __init__(self, billing_file_path: str):
        """
        Initialize GCP data source
        
        Args:
            billing_file_path: Path to GCP billing export JSON or CSV
        """
        self.file_path = billing_file_path
        # Try to load as CSV first, then JSON
        try:
            self.df = pd.read_csv(billing_file_path)
        except:
            # If CSV fails, try JSON
            with open(billing_file_path, 'r') as f:
                data = json.load(f)
            self.df = pd.json_normalize(data)
        self._schema = None
        logger.info(f"✅ Loaded GCP billing data: {billing_file_path} ({len(self.df)} rows)")
    
    def get_schema(self) -> Dict[str, Any]:
        """Discover GCP billing schema"""
        if self._schema is None:
            # Normalize GCP column names
            gcp_columns = {
                'usage_start_time': 'date',
                'service.description': 'service',
                'resource.name': 'resource_id',
                'cost': 'cost',
                'sku.description': 'usage_type',
                'location.region': 'region',
                'project.id': 'project'
            }
            
            self._schema = {
                "type": "gcp",
                "source": self.file_path,
                "columns": list(self.df.columns),
                "normalized_columns": gcp_columns,
                "row_count": len(self.df)
            }
        return self._schema
    
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate query safety"""
        if 'limit' in query_params and query_params['limit'] > 10000:
            return False
        return True
    
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query GCP billing data"""
        if not self.validate_query(query_params):
            raise ValueError("Query validation failed")
        
        df_filtered = self.df.copy()
        
        # Apply filters
        if 'filter' in query_params:
            for key, value in query_params['filter'].items():
                if key in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[key] == value]
        
        limit = query_params.get('limit', 100)
        result = df_filtered.head(limit).to_dict('records')
        
        return result


class AzureDataSource(DataSource):
    """Azure Cost Management data source adapter"""
    
    def __init__(self, billing_file_path: str):
        """
        Initialize Azure data source
        
        Args:
            billing_file_path: Path to Azure cost export CSV
        """
        self.file_path = billing_file_path
        self.df = pd.read_csv(billing_file_path)
        self._schema = None
        logger.info(f"✅ Loaded Azure billing data: {billing_file_path} ({len(self.df)} rows)")
    
    def get_schema(self) -> Dict[str, Any]:
        """Discover Azure billing schema"""
        if self._schema is None:
            # Normalize Azure column names
            azure_columns = {
                'Date': 'date',
                'ServiceName': 'service',
                'ResourceId': 'resource_id',
                'Cost': 'cost',
                'MeterCategory': 'usage_type',
                'ResourceLocation': 'region',
                'SubscriptionId': 'subscription'
            }
            
            self._schema = {
                "type": "azure",
                "source": self.file_path,
                "columns": list(self.df.columns),
                "normalized_columns": azure_columns,
                "row_count": len(self.df)
            }
        return self._schema
    
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate query safety"""
        if 'limit' in query_params and query_params['limit'] > 10000:
            return False
        return True
    
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query Azure billing data"""
        if not self.validate_query(query_params):
            raise ValueError("Query validation failed")
        
        df_filtered = self.df.copy()
        
        # Apply filters
        if 'filter' in query_params:
            for key, value in query_params['filter'].items():
                if key in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[key] == value]
        
        limit = query_params.get('limit', 100)
        result = df_filtered.head(limit).to_dict('records')
        
        return result


class MongoDBDataSource(DataSource):
    """MongoDB database data source - demonstrates heterogeneous data integration"""
    
    def __init__(self, connection_string: str, database_name: str, collection_name: str):
        """
        Initialize MongoDB data source
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
            collection_name: Collection name
        """
        try:
            from pymongo import MongoClient
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
            self._schema = None
            logger.info(f"✅ Connected to MongoDB: {database_name}.{collection_name}")
        except ImportError:
            logger.warning("⚠️ pymongo not installed. MongoDB support unavailable.")
            raise ImportError("pymongo is required for MongoDB support. Install with: pip install pymongo")
    
    def get_schema(self) -> Dict[str, Any]:
        """Discover MongoDB collection schema"""
        if self._schema is None:
            sample = self.collection.find_one()
            if sample:
                # Infer schema from sample document
                fields = {}
                for key, value in sample.items():
                    if key != '_id':
                        fields[key] = type(value).__name__
                
                self._schema = {
                    "type": "mongodb",
                    "database": self.db.name,
                    "collection": self.collection.name,
                    "fields": fields,
                    "row_count": self.collection.count_documents({})
                }
            else:
                self._schema = {
                    "type": "mongodb",
                    "database": self.db.name,
                    "collection": self.collection.name,
                    "fields": {},
                    "row_count": 0
                }
        return self._schema
    
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate MongoDB query safety"""
        # Block dangerous operations
        if 'filter' in query_params:
            filter_str = str(query_params['filter'])
            dangerous_ops = ['$where', '$eval', '$function']
            if any(op in filter_str for op in dangerous_ops):
                return False
        
        if 'limit' in query_params and query_params['limit'] > 10000:
            return False
        return True
    
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query MongoDB collection"""
        if not self.validate_query(query_params):
            raise ValueError("Query validation failed: Unsafe operation detected")
        
        filter_query = query_params.get('filter', {})
        limit = query_params.get('limit', 100)
        sort = query_params.get('sort', None)
        
        cursor = self.collection.find(filter_query)
        
        if sort:
            cursor = cursor.sort(sort)
        
        results = list(cursor.limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            if '_id' in result:
                result['_id'] = str(result['_id'])
        
        return results


class RESTAPIDataSource(DataSource):
    """REST API data source - demonstrates heterogeneous data integration"""
    
    def __init__(self, base_url: str, endpoint: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize REST API data source
        
        Args:
            base_url: Base URL of the API
            endpoint: API endpoint path
            headers: Optional HTTP headers
        """
        self.base_url = base_url.rstrip('/')
        self.endpoint = endpoint.lstrip('/')
        self.headers = headers or {}
        self._schema = None
        logger.info(f"✅ Configured REST API data source: {self.base_url}/{self.endpoint}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Discover API response schema"""
        if self._schema is None:
            try:
                # Make a test request to discover schema
                response = httpx.get(
                    f"{self.base_url}/{self.endpoint}",
                    headers=self.headers,
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                
                # Infer schema from response
                if isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                    fields = {key: type(value).__name__ for key, value in sample.items()}
                elif isinstance(data, dict):
                    fields = {key: type(value).__name__ for key, value in data.items()}
                else:
                    fields = {}
                
                self._schema = {
                    "type": "rest_api",
                    "base_url": self.base_url,
                    "endpoint": self.endpoint,
                    "fields": fields,
                    "row_count": len(data) if isinstance(data, list) else 1
                }
            except Exception as e:
                logger.warning(f"⚠️ Could not discover API schema: {e}")
                self._schema = {
                    "type": "rest_api",
                    "base_url": self.base_url,
                    "endpoint": self.endpoint,
                    "fields": {},
                    "row_count": 0
                }
        return self._schema
    
    def validate_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate API query safety"""
        # Check for dangerous endpoints
        dangerous_patterns = ['delete', 'drop', 'remove', 'admin']
        endpoint_lower = self.endpoint.lower()
        if any(pattern in endpoint_lower for pattern in dangerous_patterns):
            return False
        
        if 'limit' in query_params and query_params['limit'] > 10000:
            return False
        return True
    
    def query(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query REST API"""
        if not self.validate_query(query_params):
            raise ValueError("Query validation failed")
        
        # Build query parameters
        api_params = query_params.get('api_params', {})
        limit = query_params.get('limit', 100)
        
        # Make API request
        response = httpx.get(
            f"{self.base_url}/{self.endpoint}",
            headers=self.headers,
            params=api_params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, list):
            results = data[:limit]
        elif isinstance(data, dict):
            # Try to find a list in the response
            for key, value in data.items():
                if isinstance(value, list):
                    results = value[:limit]
                    break
            else:
                results = [data]
        else:
            results = []
        
        return results


class DataSourceRegistry:
    """Central registry for all data sources - schema-agnostic & heterogeneous interface
    
    Supports multiple data source types:
    - File-based: CSV, JSON (AWS, GCP, Azure billing files)
    - Databases: MongoDB, PostgreSQL (extensible)
    - APIs: REST APIs, GraphQL (extensible)
    - Streams: Real-time data streams (extensible)
    """
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        logger.info("✅ Data source registry initialized")
    
    def register(self, name: str, source: DataSource):
        """Register a data source"""
        self.sources[name] = source
        schema = source.get_schema()
        logger.info(f"✅ Registered data source: {name} (type: {schema.get('type', 'unknown')}, rows: {schema.get('row_count', 0)})")
    
    def get_source(self, name: str) -> Optional[DataSource]:
        """Get a data source by name"""
        return self.sources.get(name)
    
    def list_sources(self) -> List[Dict[str, Any]]:
        """List all available data sources with their schemas"""
        return [
            {
                "name": name,
                "schema": source.get_schema()
            }
            for name, source in self.sources.items()
        ]
    
    def query_source(self, source_name: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query a specific data source"""
        source = self.get_source(source_name)
        if not source:
            raise ValueError(f"Data source '{source_name}' not found")
        return source.query(query_params)
    
    def query_all_sources(self, query_params: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Query all registered data sources"""
        results = {}
        for name in self.sources.keys():
            try:
                results[name] = self.query_source(name, query_params)
            except Exception as e:
                logger.error(f"❌ Failed to query {name}: {e}")
                results[name] = []
        return results

