# services/backtest_session_cache.py

import json
import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache configuration
SESSION_CACHE_DIR = "cache/backtest_sessions"
SESSION_DURATION_DAYS = 30  # Sessions expire after 30 days
SESSION_INDEX_FILE = os.path.join(SESSION_CACHE_DIR, "sessions_index.json")


def _ensure_cache_dir():
    """Ensure cache directory exists"""
    os.makedirs(SESSION_CACHE_DIR, exist_ok=True)


def _generate_session_id(reference_date: str, filters: Dict = None) -> str:
    """Generate a unique session ID based on reference date and filters"""
    session_key = f"{reference_date}_{json.dumps(filters or {}, sort_keys=True)}"
    return hashlib.md5(session_key.encode()).hexdigest()[:16]


def create_session(
    reference_date: str,
    filters: Dict = None,
    historical_rankings: List[Dict] = None,
    selected_stocks: List[str] = None,
    trade_configs: Dict[str, Dict] = None,
    trade_results: Dict[str, Dict] = None
) -> str:
    """
    Create or update a backtesting session.
    
    Args:
        reference_date: Reference date for the backtest
        filters: Filters used for historical rankings
        historical_rankings: List of historical stock rankings
        selected_stocks: List of selected ticker symbols
        trade_configs: Dict mapping ticker to trade configuration
        trade_results: Dict mapping ticker to trade simulation results
    
    Returns:
        Session ID string
    """
    try:
        _ensure_cache_dir()
        
        session_id = _generate_session_id(reference_date, filters)
        session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        
        session_data = {
            "session_id": session_id,
            "reference_date": reference_date,
            "filters": filters or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "historical_rankings": historical_rankings or [],
            "selected_stocks": selected_stocks or [],
            "trade_configs": trade_configs or {},
            "trade_results": trade_results or {},
            "screening_strategy": None,  # Will be set when strategy is saved
            "selling_strategy": None  # Will be set when strategy is saved
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Update session index
        update_session_index(session_id, reference_date, filters)
        
        logger.info(f"💾 Created/updated session {session_id} for {reference_date}")
        return session_id
        
    except Exception as e:
        logger.error(f"❌ Error creating session: {e}")
        raise


def get_session(session_id: str) -> Optional[Dict]:
    """
    Load a backtesting session by ID.
    
    Args:
        session_id: Session ID to load
    
    Returns:
        Session data dictionary or None if not found/expired
    """
    try:
        session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            logger.warning(f"⚠️  Session {session_id} not found")
            return None
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Check if session is expired
        updated_at = datetime.fromisoformat(session_data.get('updated_at', '1970-01-01'))
        if datetime.now() - updated_at > timedelta(days=SESSION_DURATION_DAYS):
            logger.info(f"⏰ Session {session_id} expired (age: {datetime.now() - updated_at})")
            return None
        
        logger.info(f"📂 Loaded session {session_id}")
        return session_data
        
    except Exception as e:
        logger.error(f"❌ Error loading session {session_id}: {e}")
        return None


def find_session_by_date(reference_date: str, filters: Dict = None) -> Optional[Dict]:
    """
    Find a session by reference date and filters.
    
    Args:
        reference_date: Reference date to search for
        filters: Optional filters to match
    
    Returns:
        Session data dictionary or None if not found
    """
    session_id = _generate_session_id(reference_date, filters)
    return get_session(session_id)


def update_session(
    session_id: str,
    historical_rankings: List[Dict] = None,
    selected_stocks: List[str] = None,
    trade_configs: Dict[str, Dict] = None,
    trade_results: Dict[str, Dict] = None,
    screening_strategy: Dict = None,
    selling_strategy: Dict = None
) -> bool:
    """
    Update an existing session with new data.
    
    Args:
        session_id: Session ID to update
        historical_rankings: Optional new historical rankings
        selected_stocks: Optional new selected stocks list
        trade_configs: Optional new trade configurations
        trade_results: Optional new trade results
    
    Returns:
        True if update successful, False otherwise
    """
    try:
        session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            logger.warning(f"⚠️  Session {session_id} not found for update")
            return False
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Update only provided fields
        if historical_rankings is not None:
            session_data['historical_rankings'] = historical_rankings
        if selected_stocks is not None:
            session_data['selected_stocks'] = selected_stocks
        if trade_configs is not None:
            session_data['trade_configs'].update(trade_configs)
        if trade_results is not None:
            session_data['trade_results'].update(trade_results)
        if screening_strategy is not None:
            session_data['screening_strategy'] = screening_strategy
        if selling_strategy is not None:
            session_data['selling_strategy'] = selling_strategy
        
        # Ensure strategy fields exist (for backward compatibility)
        if 'screening_strategy' not in session_data:
            session_data['screening_strategy'] = None
        if 'selling_strategy' not in session_data:
            session_data['selling_strategy'] = None
        
        session_data['updated_at'] = datetime.now().isoformat()
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"💾 Updated session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating session {session_id}: {e}")
        return False


def add_trade_to_session(
    session_id: str,
    ticker: str,
    trade_config: Dict,
    trade_result: Dict
) -> bool:
    """
    Add a trade configuration and result to a session.
    
    Args:
        session_id: Session ID
        ticker: Ticker symbol
        trade_config: Trade configuration (quantity, stop_loss, take_profit, etc.)
        trade_result: Trade simulation result
    
    Returns:
        True if successful, False otherwise
    """
    try:
        session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            logger.warning(f"⚠️  Session {session_id} not found")
            return False
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Initialize if needed
        if 'trade_configs' not in session_data:
            session_data['trade_configs'] = {}
        if 'trade_results' not in session_data:
            session_data['trade_results'] = {}
        
        session_data['trade_configs'][ticker] = trade_config
        session_data['trade_results'][ticker] = trade_result
        
        # Update selected stocks if not already included
        if ticker not in session_data.get('selected_stocks', []):
            if 'selected_stocks' not in session_data:
                session_data['selected_stocks'] = []
            session_data['selected_stocks'].append(ticker)
        
        session_data['updated_at'] = datetime.now().isoformat()
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"💾 Added trade for {ticker} to session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding trade to session {session_id}: {e}")
        return False


def list_sessions() -> List[Dict]:
    """
    List all available backtesting sessions.
    
    Returns:
        List of session metadata dictionaries
    """
    try:
        _ensure_cache_dir()
        
        sessions = []
        if not os.path.exists(SESSION_INDEX_FILE):
            return sessions
        
        with open(SESSION_INDEX_FILE, 'r') as f:
            index_data = json.load(f)
        
        for session_id, metadata in index_data.items():
            session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    
                # Check expiration
                updated_at = datetime.fromisoformat(session_data.get('updated_at', '1970-01-01'))
                if datetime.now() - updated_at <= timedelta(days=SESSION_DURATION_DAYS):
                    sessions.append({
                        "session_id": session_id,
                        "reference_date": session_data.get('reference_date'),
                        "created_at": session_data.get('created_at'),
                        "updated_at": session_data.get('updated_at'),
                        "num_rankings": len(session_data.get('historical_rankings', [])),
                        "num_selected": len(session_data.get('selected_stocks', [])),
                        "num_trades": len(session_data.get('trade_results', {}))
                    })
        
        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return sessions
        
    except Exception as e:
        logger.error(f"❌ Error listing sessions: {e}")
        return []


def update_session_index(session_id: str, reference_date: str, filters: Dict = None):
    """Update the sessions index file"""
    try:
        _ensure_cache_dir()
        
        if os.path.exists(SESSION_INDEX_FILE):
            with open(SESSION_INDEX_FILE, 'r') as f:
                index_data = json.load(f)
        else:
            index_data = {}
        
        index_data[session_id] = {
            "reference_date": reference_date,
            "filters": filters or {},
            "last_updated": datetime.now().isoformat()
        }
        
        with open(SESSION_INDEX_FILE, 'w') as f:
            json.dump(index_data, f, indent=2)
            
    except Exception as e:
        logger.warning(f"⚠️  Error updating session index: {e}")


def delete_session(session_id: str) -> bool:
    """
    Delete a backtesting session.
    
    Args:
        session_id: Session ID to delete
    
    Returns:
        True if deleted, False otherwise
    """
    try:
        session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
        
        if os.path.exists(session_file):
            os.remove(session_file)
            logger.info(f"🗑️  Deleted session {session_id}")
        
        # Update index
        if os.path.exists(SESSION_INDEX_FILE):
            with open(SESSION_INDEX_FILE, 'r') as f:
                index_data = json.load(f)
            
            if session_id in index_data:
                del index_data[session_id]
                with open(SESSION_INDEX_FILE, 'w') as f:
                    json.dump(index_data, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error deleting session {session_id}: {e}")
        return False


def clear_expired_sessions():
    """Remove expired sessions from cache"""
    try:
        sessions = list_sessions()
        deleted_count = 0
        
        for session_meta in sessions:
            session_id = session_meta['session_id']
            session_file = os.path.join(SESSION_CACHE_DIR, f"{session_id}.json")
            
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                updated_at = datetime.fromisoformat(session_data.get('updated_at', '1970-01-01'))
                if datetime.now() - updated_at > timedelta(days=SESSION_DURATION_DAYS):
                    delete_session(session_id)
                    deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} expired sessions")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Error clearing expired sessions: {e}")
        return 0

