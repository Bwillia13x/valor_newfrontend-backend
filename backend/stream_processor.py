"""
Real-time Stream Processing Engine for Valor IVX Platform
Phase 9: Advanced Analytics and Machine Learning

This module provides real-time data processing capabilities including:
- Stream processing for market data
- Event-driven architecture
- Real-time analytics
- Data stream management
- Real-time dashboards
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Coroutine
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import queue
import redis
import websockets
import aiohttp
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf

from .analytics_engine import analytics_engine, MarketSignal
from .settings import settings

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Stream event data structure"""
    event_type: str
    symbol: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    priority: int = 1


@dataclass
class StreamConfig:
    """Stream configuration"""
    symbols: List[str]
    update_interval: float = 1.0  # seconds
    max_buffer_size: int = 1000
    enable_alerts: bool = True
    enable_analytics: bool = True
    data_sources: List[str] = field(default_factory=lambda: ["yfinance", "websocket"])


class StreamProcessor:
    """Real-time stream processing engine"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.config = StreamConfig(symbols=[])
        
        # Stream management
        self.active_streams = {}
        self.stream_buffers = defaultdict(lambda: deque(maxlen=1000))
        self.event_handlers = defaultdict(list)
        
        # Processing queues
        self.event_queue = asyncio.Queue()
        self.alert_queue = asyncio.Queue()
        self.analytics_queue = asyncio.Queue()
        
        # Threading
        self.processing_thread = None
        self.running = False
        
        # WebSocket connections
        self.websocket_connections = {}
        
        # Real-time data cache
        self.realtime_data = {}
        self.last_update = {}
        
        # Performance metrics
        self.metrics = {
            "events_processed": 0,
            "alerts_generated": 0,
            "analytics_runs": 0,
            "errors": 0,
            "latency_ms": []
        }
        
        logger.info("Stream Processor initialized")
    
    async def start(self, config: StreamConfig):
        """Start the stream processor"""
        self.config = config
        self.running = True
        
        # Start processing tasks
        asyncio.create_task(self._event_processor())
        asyncio.create_task(self._alert_processor())
        asyncio.create_task(self._analytics_processor())
        
        # Start data streams
        for symbol in config.symbols:
            await self._start_symbol_stream(symbol)
        
        logger.info(f"Stream processor started with {len(config.symbols)} symbols")
    
    async def stop(self):
        """Stop the stream processor"""
        self.running = False
        
        # Stop all streams
        for symbol in list(self.active_streams.keys()):
            await self._stop_symbol_stream(symbol)
        
        # Close WebSocket connections
        for ws in self.websocket_connections.values():
            await ws.close()
        
        logger.info("Stream processor stopped")
    
    async def add_symbol(self, symbol: str):
        """Add a symbol to the stream"""
        if symbol not in self.active_streams:
            await self._start_symbol_stream(symbol)
            self.config.symbols.append(symbol)
            logger.info(f"Added symbol {symbol} to stream")
    
    async def remove_symbol(self, symbol: str):
        """Remove a symbol from the stream"""
        if symbol in self.active_streams:
            await self._stop_symbol_stream(symbol)
            self.config.symbols.remove(symbol)
            logger.info(f"Removed symbol {symbol} from stream")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
    
    async def get_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time data for a symbol"""
        return self.realtime_data.get(symbol)
    
    async def get_stream_metrics(self) -> Dict[str, Any]:
        """Get stream processing metrics"""
        return {
            **self.metrics,
            "active_streams": len(self.active_streams),
            "buffer_sizes": {symbol: len(buffer) for symbol, buffer in self.stream_buffers.items()},
            "last_update": {symbol: ts.isoformat() if ts else None for symbol, ts in self.last_update.items()}
        }
    
    async def _start_symbol_stream(self, symbol: str):
        """Start streaming data for a symbol"""
        try:
            # Create stream task
            stream_task = asyncio.create_task(self._symbol_stream_loop(symbol))
            self.active_streams[symbol] = stream_task
            
            logger.info(f"Started stream for {symbol}")
            
        except Exception as e:
            logger.error(f"Error starting stream for {symbol}: {e}")
    
    async def _stop_symbol_stream(self, symbol: str):
        """Stop streaming data for a symbol"""
        if symbol in self.active_streams:
            task = self.active_streams[symbol]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_streams[symbol]
            
            logger.info(f"Stopped stream for {symbol}")
    
    async def _symbol_stream_loop(self, symbol: str):
        """Main stream loop for a symbol"""
        while self.running and symbol in self.active_streams:
            try:
                # Fetch real-time data
                data = await self._fetch_realtime_data(symbol)
                if data:
                    # Create stream event
                    event = StreamEvent(
                        event_type="price_update",
                        symbol=symbol,
                        data=data,
                        timestamp=datetime.utcnow(),
                        source="yfinance"
                    )
                    
                    # Add to event queue
                    await self.event_queue.put(event)
                    
                    # Update real-time data cache
                    self.realtime_data[symbol] = data
                    self.last_update[symbol] = datetime.utcnow()
                    
                    # Add to buffer
                    self.stream_buffers[symbol].append(data)
                
                # Wait for next update
                await asyncio.sleep(self.config.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stream loop for {symbol}: {e}")
                self.metrics["errors"] += 1
                await asyncio.sleep(self.config.update_interval)
    
    async def _fetch_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch real-time data for a symbol"""
        try:
            # Use yfinance for real-time data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent price data
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            data = {
                "symbol": symbol,
                "price": current_price,
                "change": current_price - previous_price,
                "change_percent": ((current_price / previous_price - 1) * 100) if previous_price != 0 else 0,
                "volume": hist['Volume'].iloc[-1] if not hist.empty else 0,
                "high": hist['High'].max(),
                "low": hist['Low'].min(),
                "open": hist['Open'].iloc[0],
                "market_cap": info.get('marketCap', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {e}")
            return None
    
    async def _event_processor(self):
        """Process stream events"""
        while self.running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                start_time = time.time()
                
                # Process event
                await self._process_event(event)
                
                # Update metrics
                self.metrics["events_processed"] += 1
                latency = (time.time() - start_time) * 1000
                self.metrics["latency_ms"].append(latency)
                
                # Keep only recent latency measurements
                if len(self.metrics["latency_ms"]) > 100:
                    self.metrics["latency_ms"] = self.metrics["latency_ms"][-100:]
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                self.metrics["errors"] += 1
    
    async def _process_event(self, event: StreamEvent):
        """Process a single event"""
        try:
            # Call registered handlers
            handlers = self.event_handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
            
            # Check for alerts
            if self.config.enable_alerts:
                await self.alert_queue.put(event)
            
            # Run analytics if enabled
            if self.config.enable_analytics:
                await self.analytics_queue.put(event)
                
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def _alert_processor(self):
        """Process alerts from stream events"""
        while self.running:
            try:
                # Get event from alert queue
                event = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                
                # Generate alerts
                alerts = await self._generate_alerts(event)
                
                # Send alerts
                for alert in alerts:
                    await self._send_alert(alert)
                
                self.metrics["alerts_generated"] += len(alerts)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in alert processor: {e}")
                self.metrics["errors"] += 1
    
    async def _analytics_processor(self):
        """Process analytics from stream events"""
        while self.running:
            try:
                # Get event from analytics queue
                event = await asyncio.wait_for(self.analytics_queue.get(), timeout=1.0)
                
                # Run real-time analytics
                await self._run_realtime_analytics(event)
                
                self.metrics["analytics_runs"] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in analytics processor: {e}")
                self.metrics["errors"] += 1
    
    async def _generate_alerts(self, event: StreamEvent) -> List[Dict[str, Any]]:
        """Generate alerts based on event data"""
        alerts = []
        
        try:
            if event.event_type == "price_update":
                data = event.data
                
                # Price change alerts
                change_percent = data.get("change_percent", 0)
                if abs(change_percent) > 5:  # 5% threshold
                    alerts.append({
                        "type": "price_alert",
                        "symbol": event.symbol,
                        "message": f"{event.symbol} moved {change_percent:.2f}%",
                        "severity": "high" if abs(change_percent) > 10 else "medium",
                        "data": data,
                        "timestamp": event.timestamp.isoformat()
                    })
                
                # Volume alerts
                volume_ratio = data.get("volume_ratio", 1)
                if volume_ratio > 2:  # 2x average volume
                    alerts.append({
                        "type": "volume_alert",
                        "symbol": event.symbol,
                        "message": f"{event.symbol} volume spike detected",
                        "severity": "medium",
                        "data": data,
                        "timestamp": event.timestamp.isoformat()
                    })
                
                # Technical indicator alerts
                technical_alerts = await self._check_technical_indicators(event.symbol, data)
                alerts.extend(technical_alerts)
        
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
        
        return alerts
    
    async def _check_technical_indicators(self, symbol: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check technical indicators for alerts"""
        alerts = []
        
        try:
            # Get historical data for technical analysis
            historical_data = await analytics_engine._get_historical_data(symbol, "5d")
            if historical_data is None or historical_data.empty:
                return alerts
            
            current_price = data.get("price", 0)
            
            # RSI analysis
            if len(historical_data) >= 14:
                delta = historical_data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                if current_rsi < 30:
                    alerts.append({
                        "type": "technical_alert",
                        "symbol": symbol,
                        "message": f"{symbol} RSI oversold: {current_rsi:.2f}",
                        "severity": "medium",
                        "indicator": "rsi",
                        "value": current_rsi,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif current_rsi > 70:
                    alerts.append({
                        "type": "technical_alert",
                        "symbol": symbol,
                        "message": f"{symbol} RSI overbought: {current_rsi:.2f}",
                        "severity": "medium",
                        "indicator": "rsi",
                        "value": current_rsi,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Moving average crossovers
            if len(historical_data) >= 50:
                sma_20 = historical_data['Close'].rolling(window=20).mean()
                sma_50 = historical_data['Close'].rolling(window=50).mean()
                
                current_sma_20 = sma_20.iloc[-1]
                current_sma_50 = sma_50.iloc[-1]
                prev_sma_20 = sma_20.iloc[-2] if len(sma_20) > 1 else current_sma_20
                prev_sma_50 = sma_50.iloc[-2] if len(sma_50) > 1 else current_sma_50
                
                # Golden cross
                if current_sma_20 > current_sma_50 and prev_sma_20 <= prev_sma_50:
                    alerts.append({
                        "type": "technical_alert",
                        "symbol": symbol,
                        "message": f"{symbol} Golden cross detected",
                        "severity": "high",
                        "indicator": "moving_average",
                        "value": "golden_cross",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                # Death cross
                elif current_sma_20 < current_sma_50 and prev_sma_20 >= prev_sma_50:
                    alerts.append({
                        "type": "technical_alert",
                        "symbol": symbol,
                        "message": f"{symbol} Death cross detected",
                        "severity": "high",
                        "indicator": "moving_average",
                        "value": "death_cross",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        except Exception as e:
            logger.error(f"Error checking technical indicators: {e}")
        
        return alerts
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert to subscribers"""
        try:
            # Store alert in Redis if available
            if self.redis_client:
                alert_key = f"alerts:{alert['symbol']}:{int(time.time())}"
                self.redis_client.setex(alert_key, 3600, json.dumps(alert))  # 1 hour TTL
            
            # Log alert
            logger.info(f"Alert: {alert['message']}")
            
            # TODO: Send to WebSocket subscribers, email, SMS, etc.
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def _run_realtime_analytics(self, event: StreamEvent):
        """Run real-time analytics on event data"""
        try:
            if event.event_type == "price_update":
                # Update sentiment analysis
                sentiment = await analytics_engine.analyze_market_sentiment(event.symbol)
                
                # Generate market signals
                signals = await analytics_engine.generate_market_signals(event.symbol)
                
                # Store analytics results
                analytics_result = {
                    "symbol": event.symbol,
                    "sentiment": sentiment.overall_sentiment,
                    "signals": [signal.__dict__ for signal in signals],
                    "timestamp": event.timestamp.isoformat()
                }
                
                # Store in Redis if available
                if self.redis_client:
                    analytics_key = f"analytics:{event.symbol}:{int(time.time())}"
                    self.redis_client.setex(analytics_key, 1800, json.dumps(analytics_result))  # 30 min TTL
        
        except Exception as e:
            logger.error(f"Error running real-time analytics: {e}")
    
    async def get_stream_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get stream history for a symbol"""
        buffer = self.stream_buffers.get(symbol, deque())
        return list(buffer)[-limit:]
    
    async def get_all_realtime_data(self) -> Dict[str, Any]:
        """Get real-time data for all symbols"""
        return {
            "data": self.realtime_data,
            "last_update": {symbol: ts.isoformat() if ts else None for symbol, ts in self.last_update.items()},
            "timestamp": datetime.utcnow().isoformat()
        }


class WebSocketStreamManager:
    """WebSocket-based stream manager for real-time data"""
    
    def __init__(self, stream_processor: StreamProcessor):
        self.stream_processor = stream_processor
        self.connections = set()
        self.symbol_subscriptions = defaultdict(set)
        
    async def handle_connection(self, websocket, path):
        """Handle WebSocket connection"""
        self.connections.add(websocket)
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._remove_connection(websocket)
    
    async def _handle_message(self, websocket, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                symbols = data.get("symbols", [])
                for symbol in symbols:
                    self.symbol_subscriptions[symbol].add(websocket)
                    await self.stream_processor.add_symbol(symbol)
                
                await websocket.send(json.dumps({
                    "type": "subscribed",
                    "symbols": symbols
                }))
            
            elif message_type == "unsubscribe":
                symbols = data.get("symbols", [])
                for symbol in symbols:
                    self.symbol_subscriptions[symbol].discard(websocket)
                
                await websocket.send(json.dumps({
                    "type": "unsubscribed",
                    "symbols": symbols
                }))
            
            elif message_type == "get_data":
                symbol = data.get("symbol")
                if symbol:
                    realtime_data = await self.stream_processor.get_realtime_data(symbol)
                    await websocket.send(json.dumps({
                        "type": "data",
                        "symbol": symbol,
                        "data": realtime_data
                    }))
        
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await websocket.send(json.dumps({"error": str(e)}))
    
    async def _remove_connection(self, websocket):
        """Remove WebSocket connection"""
        self.connections.discard(websocket)
        
        # Remove from all symbol subscriptions
        for symbol, connections in self.symbol_subscriptions.items():
            connections.discard(websocket)
    
    async def broadcast_data(self, symbol: str, data: Dict[str, Any]):
        """Broadcast data to all subscribers of a symbol"""
        message = json.dumps({
            "type": "data_update",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send to all subscribers
        disconnected = set()
        for websocket in self.symbol_subscriptions[symbol]:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected connections
        for websocket in disconnected:
            await self._remove_connection(websocket)


# Global stream processor instance
stream_processor = StreamProcessor()
websocket_manager = WebSocketStreamManager(stream_processor) 