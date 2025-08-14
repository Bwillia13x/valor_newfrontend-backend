"""
Enhanced Pagination utilities for API endpoints with security and performance optimizations
Phase 4: Performance & Scalability - Enhanced Security Edition
"""

from typing import Dict, Any, List, Optional, Tuple
from flask import request, g
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc, or_
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PaginationConfig:
    """Enhanced configuration for pagination with security limits"""
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MAX_TOTAL_PAGES = 1000  # Prevent deep pagination attacks
    DEFAULT_SORT_FIELD = "created_at"
    DEFAULT_SORT_ORDER = "desc"
    
    # Allowed sort fields per model to prevent SQL injection
    ALLOWED_SORT_FIELDS = {
        'Run': ['created_at', 'updated_at', 'ticker', 'valuation'],
        'Scenario': ['created_at', 'updated_at', 'name'],
        'LBORun': ['created_at', 'updated_at', 'company_name'],
        'LBOScenario': ['created_at', 'updated_at', 'name'],
        'MARun': ['created_at', 'updated_at', 'target_company'],
        'MAScenario': ['created_at', 'updated_at', 'name'],
        'User': ['created_at', 'updated_at', 'username', 'email'],
        'Organization': ['created_at', 'updated_at', 'name']
    }


def get_pagination_params(model_name: Optional[str] = None) -> Tuple[int, int, str, str]:
    """
    Extract and validate pagination parameters from request with security checks.
    
    Args:
        model_name: Name of the model to validate sort fields against
    
    Returns:
        Tuple of (page, per_page, sort_field, sort_order)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', PaginationConfig.DEFAULT_PAGE_SIZE, type=int)
    sort_field = request.args.get('sort_by', PaginationConfig.DEFAULT_SORT_FIELD, type=str)
    sort_order = request.args.get('sort_order', PaginationConfig.DEFAULT_SORT_ORDER, type=str)
    
    # Validate and constrain parameters with security limits
    page = max(1, min(page, PaginationConfig.MAX_TOTAL_PAGES))  # Prevent deep pagination
    per_page = min(max(1, per_page), PaginationConfig.MAX_PAGE_SIZE)
    sort_order = sort_order.lower() if sort_order.lower() in ['asc', 'desc'] else 'desc'
    
    # Validate sort field to prevent SQL injection
    if model_name and model_name in PaginationConfig.ALLOWED_SORT_FIELDS:
        allowed_fields = PaginationConfig.ALLOWED_SORT_FIELDS[model_name]
        if sort_field not in allowed_fields:
            logger.warning(
                f"Invalid sort field '{sort_field}' for model '{model_name}'. Using default.",
                extra={
                    'correlation_id': getattr(g, 'request_id', None),
                    'attempted_sort_field': sort_field,
                    'model_name': model_name,
                    'allowed_fields': allowed_fields
                }
            )
            sort_field = PaginationConfig.DEFAULT_SORT_FIELD
    
    # Sanitize sort field to prevent SQL injection
    sort_field = ''.join(c for c in sort_field if c.isalnum() or c == '_')
    
    return page, per_page, sort_field, sort_order


def apply_pagination(query: Query, model_class) -> Tuple[Query, Dict[str, Any]]:
    """
    Apply pagination to a SQLAlchemy query with enhanced security and performance monitoring.
    
    Args:
        query: SQLAlchemy query to paginate
        model_class: Model class for validation
        
    Returns:
        Tuple of (paginated_query, pagination_info)
    """
    start_time = datetime.now(timezone.utc)
    model_name = model_class.__name__
    
    # Get validated pagination parameters
    page, per_page, sort_field, sort_order = get_pagination_params(model_name)
    
    # Count total records for performance monitoring
    total_count = query.count()
    
    # Log large dataset warnings
    if total_count > 10000:
        logger.warning(
            f"Large dataset pagination: {total_count} records for {model_name}",
            extra={
                'correlation_id': getattr(g, 'request_id', None),
                'model_name': model_name,
                'total_count': total_count,
                'user_id': getattr(g, 'user_id', None)
            }
        )
    
    # Validate sort field exists in model
    if hasattr(model_class, sort_field):
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(model_class, sort_field)))
        else:
            query = query.order_by(asc(getattr(model_class, sort_field)))
    else:
        # Fallback to default sorting
        if hasattr(model_class, PaginationConfig.DEFAULT_SORT_FIELD):
            if sort_order == 'desc':
                query = query.order_by(desc(getattr(model_class, PaginationConfig.DEFAULT_SORT_FIELD)))
            else:
                query = query.order_by(asc(getattr(model_class, PaginationConfig.DEFAULT_SORT_FIELD)))
    
    # Apply pagination with security limits
    try:
        paginated_query = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False,
            max_per_page=PaginationConfig.MAX_PAGE_SIZE
        )
    except Exception as e:
        logger.error(
            f"Pagination failed for {model_name}: {str(e)}",
            extra={
                'correlation_id': getattr(g, 'request_id', None),
                'model_name': model_name,
                'error': str(e),
                'page': page,
                'per_page': per_page
            }
        )
        raise
    
    # Calculate performance metrics
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    # Log performance metrics
    logger.info(
        f"Pagination completed for {model_name}: {len(paginated_query.items)} items in {duration:.3f}s",
        extra={
            'correlation_id': getattr(g, 'request_id', None),
            'model_name': model_name,
            'duration_seconds': duration,
            'items_returned': len(paginated_query.items),
            'total_items': paginated_query.total,
            'page': page,
            'per_page': per_page
        }
    )
    
    # Build enhanced pagination info
    pagination_info = {
        "page": page,
        "per_page": per_page,
        "total": paginated_query.total,
        "pages": paginated_query.pages,
        "has_next": paginated_query.has_next,
        "has_prev": paginated_query.has_prev,
        "next_num": paginated_query.next_num,
        "prev_num": paginated_query.prev_num,
        "sort_by": sort_field,
        "sort_order": sort_order,
        "query_time_ms": int(duration * 1000)
    }
    
    return paginated_query, pagination_info


def create_paginated_response(items: List[Any], pagination_info: Dict[str, Any], 
                            data_key: str = "items") -> Dict[str, Any]:
    """
    Create a standardized paginated response.
    
    Args:
        items: List of items to include in response
        pagination_info: Pagination metadata
        data_key: Key name for the items array
        
    Returns:
        Standardized paginated response
    """
    return {
        "success": True,
        "data": {
            data_key: items,
            "pagination": pagination_info
        }
    }


def apply_tenant_filter(query: Query, tenant_id: int) -> Query:
    """
    Apply tenant filter to a query for multi-tenant data isolation.
    
    Args:
        query: SQLAlchemy query
        tenant_id: Tenant ID to filter by
        
    Returns:
        Query with tenant filter applied
    """
    return query.filter_by(tenant_id=tenant_id)


def apply_user_filter(query: Query, user_id: int) -> Query:
    """
    Apply user filter to a query.
    
    Args:
        query: SQLAlchemy query
        user_id: User ID to filter by
        
    Returns:
        Query with user filter applied
    """
    return query.filter_by(user_id=user_id)


def apply_search_filter(query: Query, model_class, search_field: str, search_term: str) -> Query:
    """
    Apply search filter to a query.
    
    Args:
        query: SQLAlchemy query
        model_class: Model class
        search_field: Field to search in
        search_term: Search term
        
    Returns:
        Query with search filter applied
    """
    if hasattr(model_class, search_field) and search_term:
        field = getattr(model_class, search_field)
        return query.filter(field.ilike(f"%{search_term}%"))
    return query


def get_search_params() -> Tuple[Optional[str], Optional[str]]:
    """
    Extract search parameters from request.
    
    Returns:
        Tuple of (search_field, search_term)
    """
    search_field = request.args.get('search_field', type=str)
    search_term = request.args.get('search_term', type=str)
    return search_field, search_term 