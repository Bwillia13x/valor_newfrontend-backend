"""
Pagination utilities for API endpoints
Phase 4: Performance & Scalability
"""

from typing import Dict, Any, List, Optional, Tuple
from flask import request
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc


class PaginationConfig:
    """Configuration for pagination"""
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    DEFAULT_SORT_FIELD = "created_at"
    DEFAULT_SORT_ORDER = "desc"


def get_pagination_params() -> Tuple[int, int, str, str]:
    """
    Extract pagination parameters from request.
    
    Returns:
        Tuple of (page, per_page, sort_field, sort_order)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', PaginationConfig.DEFAULT_PAGE_SIZE, type=int)
    sort_field = request.args.get('sort_by', PaginationConfig.DEFAULT_SORT_FIELD, type=str)
    sort_order = request.args.get('sort_order', PaginationConfig.DEFAULT_SORT_ORDER, type=str)
    
    # Validate and constrain parameters
    page = max(1, page)
    per_page = min(max(1, per_page), PaginationConfig.MAX_PAGE_SIZE)
    sort_order = sort_order.lower() if sort_order.lower() in ['asc', 'desc'] else 'desc'
    
    return page, per_page, sort_field, sort_order


def apply_pagination(query: Query, model_class) -> Tuple[Query, Dict[str, Any]]:
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query to paginate
        model_class: Model class for validation
        
    Returns:
        Tuple of (paginated_query, pagination_info)
    """
    page, per_page, sort_field, sort_order = get_pagination_params()
    
    # Validate sort field exists in model
    if hasattr(model_class, sort_field):
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(model_class, sort_field)))
        else:
            query = query.order_by(asc(getattr(model_class, sort_field)))
    else:
        # Fallback to default sorting
        if sort_order == 'desc':
            query = query.order_by(desc(getattr(model_class, PaginationConfig.DEFAULT_SORT_FIELD)))
        else:
            query = query.order_by(asc(getattr(model_class, PaginationConfig.DEFAULT_SORT_FIELD)))
    
    # Apply pagination
    paginated_query = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
        max_per_page=PaginationConfig.MAX_PAGE_SIZE
    )
    
    # Build pagination info
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
        "sort_order": sort_order
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