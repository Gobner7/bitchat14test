#!/usr/bin/env python3
"""
CSFloat Auto-Flipper v2.0
Advanced automated trading bot with AI-powered predictions and microsecond sniping
"""

import asyncio
import signal
import sys
from datetime import datetime
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import uvloop

from config import config
from core.websocket_manager import UltraFastWebSocketManager
from core.ai_predictor import AdvancedAIPredictor
from core.sniper_engine import UltraFastSniper
from core.strategy_manager import DynamicStrategyManager
from database.market_data import MarketDataStore
from database.portfolio import PortfolioManager
from monitoring.dashboard import MonitoringDashboard
from utils.logger import get_logger, log_trade
from utils.performance import monitor, optimize_memory

# Set up uvloop for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = get_logger(__name__)
console = Console()

class CSFloatAutoFlipper:
    """Main application class"""
    
    def __init__(self):
        self.ws_manager = None
        self.ai_predictor = None
        self.sniper = None
        self.strategy_manager = None
        self.market_data = None
        self.portfolio = None
        self.dashboard = None
        self.running = False
        
    async def initialize(self):
        """Initialize all components"""
        console.print(Panel.fit(
            "[bold cyan]CSFloat Auto-Flipper v2.0[/bold cyan]\n"
            "[green]Initializing components...[/green]",
            title="Startup"
        ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Initialize database
            task = progress.add_task("Initializing databases...", total=2)
            self.market_data = MarketDataStore()
            await self.market_data.initialize()
            progress.update(task, advance=1)
            
            self.portfolio = PortfolioManager()
            await self.portfolio.initialize()
            progress.update(task, advance=1)
            
            # Initialize AI predictor
            task = progress.add_task("Loading AI models...", total=1)
            self.ai_predictor = AdvancedAIPredictor(self.market_data)
            progress.update(task, advance=1)
            
            # Initialize strategy manager
            task = progress.add_task("Configuring strategies...", total=1)
            self.strategy_manager = DynamicStrategyManager(self.portfolio)
            progress.update(task, advance=1)
            
            # Initialize WebSocket manager
            task = progress.add_task("Connecting to market...", total=1)
            self.ws_manager = UltraFastWebSocketManager()
            await self.ws_manager.connect()
            progress.update(task, advance=1)
            
            # Initialize sniper engine
            task = progress.add_task("Starting sniper engine...", total=1)
            self.sniper = UltraFastSniper(self.ws_manager, self.ai_predictor)
            progress.update(task, advance=1)
            
            # Initialize monitoring
            task = progress.add_task("Starting monitoring...", total=1)
            self.dashboard = MonitoringDashboard(
                self.portfolio, self.strategy_manager, self.market_data
            )
            await self.dashboard.start()
            progress.update(task, advance=1)
            
        # Set up main trading loop
        self._setup_trading_callbacks()
        
        console.print(Panel.fit(
            "[bold green]✓ All systems operational[/bold green]\n"
            f"[cyan]Balance: ${config.max_budget:,.2f}[/cyan]\n"
            f"[yellow]Strategies: {len(self.strategy_manager.strategies)} active[/yellow]\n"
            f"[magenta]Monitoring: http://localhost:{config.prometheus_port}/dashboard[/magenta]",
            title="Ready"
        ))
        
    def _setup_trading_callbacks(self):
        """Set up trading callbacks"""
        # WebSocket callbacks
        self.ws_manager.register_callback('listing.new', self._handle_new_listing)
        self.ws_manager.register_callback('listing.update', self._handle_listing_update)
        self.ws_manager.register_callback('listing.sold', self._handle_listing_sold)
        self.ws_manager.register_callback('market.stats', self._handle_market_stats)
        
    async def _handle_new_listing(self, message):
        """Handle new listing"""
        try:
            listing = message.data
            self.dashboard.record_websocket_message('listing.new')
            
            # Store listing
            await self.market_data.store_listing(listing)
            
            # Sniper will handle the rest
            
        except Exception as e:
            logger.error(f"New listing handler error: {e}")
            
    async def _handle_listing_update(self, message):
        """Handle listing update"""
        try:
            update = message.data
            self.dashboard.record_websocket_message('listing.update')
            
            # Check if we have a position
            position = await self.portfolio.get_position_by_listing(update.get('id'))
            if position:
                await self.portfolio.update_position_price(
                    position['_id'], 
                    update.get('price', position['current_price'])
                )
                
        except Exception as e:
            logger.error(f"Listing update handler error: {e}")
            
    async def _handle_listing_sold(self, message):
        """Handle sold listing"""
        try:
            sold_data = message.data
            self.dashboard.record_websocket_message('listing.sold')
            
            # Record trade data
            await self.market_data.store_trade(sold_data)
            
        except Exception as e:
            logger.error(f"Listing sold handler error: {e}")
            
    async def _handle_market_stats(self, message):
        """Handle market statistics"""
        try:
            stats = message.data
            self.dashboard.record_websocket_message('market.stats')
            
            # Update market trends
            # Could implement market analysis here
            
        except Exception as e:
            logger.error(f"Market stats handler error: {e}")
            
    async def run(self):
        """Main trading loop"""
        self.running = True
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._portfolio_manager()),
            asyncio.create_task(self._performance_monitor()),
            asyncio.create_task(self._cleanup_task())
        ]
        
        try:
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        finally:
            self.running = False
            
            # Cancel tasks
            for task in tasks:
                task.cancel()
                
            await self.shutdown()
            
    async def _portfolio_manager(self):
        """Manage portfolio positions"""
        while self.running:
            try:
                # Check positions for stop loss / take profit
                positions = await self.portfolio.get_open_positions()
                
                for position in positions:
                    # Get strategy parameters
                    strategy = self.strategy_manager.strategies.get(position['strategy'])
                    if not strategy:
                        continue
                        
                    # Check exit conditions
                    profit_pct = position.get('profit_percentage', 0)
                    hold_time = (datetime.utcnow() - position['open_time']).total_seconds() / 3600
                    
                    should_close = False
                    reason = ''
                    
                    # Take profit
                    if profit_pct >= config.take_profit_percentage * 100:
                        should_close = True
                        reason = 'take_profit'
                        
                    # Stop loss
                    elif profit_pct <= -config.stop_loss_percentage * 100:
                        should_close = True
                        reason = 'stop_loss'
                        
                    # Time-based exit
                    elif hold_time > config.position_timeout / 3600:
                        should_close = True
                        reason = 'timeout'
                        
                    if should_close:
                        current_price = position.get('current_price', position['buy_price'])
                        result = await self.portfolio.close_position(
                            position['_id'],
                            current_price,
                            reason
                        )
                        
                        # Update strategy performance
                        await self.strategy_manager.update_strategy_performance(
                            position['strategy'],
                            {
                                'profit': result['profit'],
                                'profit_margin': result['profit_percentage'] / 100,
                                'cost': position['buy_price'],
                                'hold_time': result['hold_time']
                            }
                        )
                        
                        # Log trade
                        log_trade(
                            'SELL',
                            position['market_hash_name'],
                            current_price,
                            result['profit'],
                            reason=reason
                        )
                        
                        # Record metrics
                        self.dashboard.record_trade(
                            'sell',
                            position['strategy'],
                            result['profit'] > 0
                        )
                        
            except Exception as e:
                logger.error(f"Portfolio manager error: {e}")
                
            await asyncio.sleep(10)  # Check every 10 seconds
            
    async def _performance_monitor(self):
        """Monitor and log performance"""
        while self.running:
            try:
                # Get performance stats
                stats = monitor.get_stats()
                portfolio_value = await self.portfolio.get_portfolio_value()
                
                # Log stats
                logger.info(
                    f"Performance - Balance: ${portfolio_value['cash_balance']:,.2f} | "
                    f"Positions: {portfolio_value['positions_count']} | "
                    f"Unrealized P/L: ${portfolio_value['unrealized_profit']:,.2f} | "
                    f"Latency: {stats.get('avg_latency', 0):.1f}ms"
                )
                
                # Optimize memory if needed
                if stats.get('memory_percent', 0) > 80:
                    optimize_memory()
                    
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def _cleanup_task(self):
        """Periodic cleanup tasks"""
        while self.running:
            try:
                # Clean up old positions
                await self.portfolio.cleanup_old_positions(days=7)
                
                # Optimize memory
                optimize_memory()
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                
            await asyncio.sleep(3600)  # Every hour
            
    async def shutdown(self):
        """Graceful shutdown"""
        console.print("\n[yellow]Shutting down...[/yellow]")
        
        # Close all positions with market orders
        positions = await self.portfolio.get_open_positions()
        if positions:
            console.print(f"[yellow]Closing {len(positions)} open positions...[/yellow]")
            for position in positions:
                try:
                    await self.portfolio.close_position(
                        position['_id'],
                        position.get('current_price', position['buy_price']),
                        reason='shutdown'
                    )
                except Exception as e:
                    logger.error(f"Error closing position: {e}")
                    
        # Close components
        if self.ws_manager:
            await self.ws_manager.close()
        if self.market_data:
            await self.market_data.close()
        if self.portfolio:
            await self.portfolio.close()
            
        console.print("[green]✓ Shutdown complete[/green]")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CSFloat Auto-Flipper')
    parser.add_argument('--dry-run', action='store_true', help='Run without executing trades')
    parser.add_argument('--config', type=str, help='Config file path')
    args = parser.parse_args()
    
    # ASCII art banner
    console.print("""
[bold cyan]
 ██████╗███████╗███████╗██╗      ██████╗  █████╗ ████████╗
██╔════╝██╔════╝██╔════╝██║     ██╔═══██╗██╔══██╗╚══██╔══╝
██║     ███████╗█████╗  ██║     ██║   ██║███████║   ██║   
██║     ╚════██║██╔══╝  ██║     ██║   ██║██╔══██║   ██║   
╚██████╗███████║██║     ███████╗╚██████╔╝██║  ██║   ██║   
 ╚═════╝╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
[/bold cyan]
[bold green]Auto-Flipper v2.0 - AI-Powered Trading Bot[/bold green]
""")
    
    # Check API key
    if not config.api_key:
        console.print("[bold red]Error: CSFLOAT_API_KEY not set![/bold red]")
        console.print("Please set your API key in the .env file")
        sys.exit(1)
        
    # Create and run flipper
    flipper = CSFloatAutoFlipper()
    
    try:
        await flipper.initialize()
        await flipper.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
    finally:
        await flipper.shutdown()

if __name__ == "__main__":
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    asyncio.run(main())