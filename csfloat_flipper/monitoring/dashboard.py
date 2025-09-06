import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, Summary
from aiohttp import web
import json
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Prometheus metrics
trade_counter = Counter('trades_total', 'Total number of trades', ['status', 'strategy'])
profit_gauge = Gauge('profit_total', 'Total profit')
balance_gauge = Gauge('balance_current', 'Current balance')
positions_gauge = Gauge('positions_open', 'Number of open positions')
latency_histogram = Histogram('operation_latency_ms', 'Operation latency in milliseconds', 
                             ['operation'], buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000])
websocket_messages = Counter('websocket_messages_total', 'Total WebSocket messages', ['type'])
snipe_attempts = Counter('snipe_attempts_total', 'Total snipe attempts', ['result'])

class MonitoringDashboard:
    """Real-time monitoring dashboard with metrics and alerts"""
    
    def __init__(self, portfolio_manager, strategy_manager, market_data):
        self.portfolio = portfolio_manager
        self.strategies = strategy_manager
        self.market_data = market_data
        self.console = Console()
        self.app = web.Application()
        self.setup_routes()
        
        # Metrics storage
        self.metrics_history = {
            'profit': [],
            'balance': [],
            'trades': [],
            'latency': [],
            'success_rate': []
        }
        
        # Alert thresholds
        self.alerts = {
            'low_balance': config.max_budget * 0.1,
            'high_loss': config.max_budget * config.max_daily_loss,
            'low_success_rate': 0.3,
            'high_latency': 500  # ms
        }
        
    def setup_routes(self):
        """Setup web routes for dashboard"""
        self.app.router.add_get('/metrics', self.prometheus_metrics)
        self.app.router.add_get('/dashboard', self.web_dashboard)
        self.app.router.add_get('/api/stats', self.api_stats)
        self.app.router.add_get('/api/positions', self.api_positions)
        self.app.router.add_get('/api/strategies', self.api_strategies)
        
    async def start(self):
        """Start monitoring services"""
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', config.prometheus_port)
        await site.start()
        
        # Start monitoring tasks
        asyncio.create_task(self._update_metrics())
        asyncio.create_task(self._check_alerts())
        asyncio.create_task(self._console_dashboard())
        
        logger.info(f"Monitoring dashboard started on port {config.prometheus_port}")
        
    async def prometheus_metrics(self, request):
        """Prometheus metrics endpoint"""
        metrics = prometheus_client.generate_latest()
        return web.Response(text=metrics.decode('utf-8'), 
                          content_type='text/plain; version=0.0.4')
        
    async def web_dashboard(self, request):
        """Web dashboard endpoint"""
        html = self._generate_dashboard_html()
        return web.Response(text=html, content_type='text/html')
        
    async def api_stats(self, request):
        """API endpoint for statistics"""
        stats = await self._get_current_stats()
        return web.json_response(stats)
        
    async def api_positions(self, request):
        """API endpoint for positions"""
        positions = await self.portfolio.get_open_positions()
        return web.json_response(positions)
        
    async def api_strategies(self, request):
        """API endpoint for strategies"""
        strategies = await self.strategies.get_active_strategies()
        return web.json_response(strategies)
        
    async def _update_metrics(self):
        """Update Prometheus metrics"""
        while True:
            try:
                # Portfolio metrics
                portfolio_value = await self.portfolio.get_portfolio_value()
                balance_gauge.set(portfolio_value['cash_balance'])
                positions_gauge.set(portfolio_value['positions_count'])
                
                # Performance metrics
                perf_stats = await self.portfolio.get_performance_stats(days=1)
                if perf_stats['total_trades'] > 0:
                    profit_gauge.set(perf_stats['total_profit'])
                    
                # Update history
                self.metrics_history['balance'].append({
                    'timestamp': datetime.now(),
                    'value': portfolio_value['cash_balance']
                })
                
                # Trim history
                for key in self.metrics_history:
                    if len(self.metrics_history[key]) > 1000:
                        self.metrics_history[key] = self.metrics_history[key][-1000:]
                        
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                
            await asyncio.sleep(10)
            
    async def _check_alerts(self):
        """Check for alert conditions"""
        while True:
            try:
                # Check balance
                balance = await self.portfolio.get_available_budget()
                if balance < self.alerts['low_balance']:
                    await self._send_alert('LOW_BALANCE', f'Balance below ${self.alerts["low_balance"]}')
                    
                # Check daily loss
                daily_stats = await self.portfolio.get_performance_stats(days=1)
                if daily_stats['total_profit'] < -self.alerts['high_loss']:
                    await self._send_alert('HIGH_LOSS', f'Daily loss exceeds limit')
                    
                # Check success rate
                if daily_stats['total_trades'] > 10:
                    if daily_stats['success_rate'] < self.alerts['low_success_rate']:
                        await self._send_alert('LOW_SUCCESS', f'Success rate: {daily_stats["success_rate"]:.1%}')
                        
            except Exception as e:
                logger.error(f"Alert check error: {e}")
                
            await asyncio.sleep(60)
            
    async def _send_alert(self, alert_type: str, message: str):
        """Send alert notification"""
        logger.warning(f"🚨 ALERT [{alert_type}]: {message}")
        
        # Could implement email/SMS/Discord notifications here
        
    async def _console_dashboard(self):
        """Rich console dashboard"""
        with Live(self._generate_console_layout(), refresh_per_second=1) as live:
            while True:
                live.update(self._generate_console_layout())
                await asyncio.sleep(1)
                
    def _generate_console_layout(self) -> Layout:
        """Generate console dashboard layout"""
        layout = Layout()
        
        # Header
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header content
        layout["header"].update(
            Panel(
                f"[bold cyan]CSFloat Auto-Flipper v2.0[/bold cyan] | "
                f"[green]Status: ACTIVE[/green] | "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style="bold"
            )
        )
        
        # Body sections
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="positions", ratio=1),
            Layout(name="strategies", ratio=1)
        )
        
        # Update sections
        asyncio.create_task(self._update_console_sections(layout))
        
        return layout
        
    async def _update_console_sections(self, layout: Layout):
        """Update console dashboard sections"""
        try:
            # Stats section
            stats = await self._get_current_stats()
            stats_table = Table(title="Portfolio Stats", show_header=False)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Balance", f"${stats['balance']:,.2f}")
            stats_table.add_row("Today's Profit", f"${stats['daily_profit']:,.2f}")
            stats_table.add_row("Open Positions", str(stats['open_positions']))
            stats_table.add_row("Success Rate", f"{stats['success_rate']:.1%}")
            stats_table.add_row("Avg Latency", f"{stats['avg_latency']:.1f}ms")
            
            layout["stats"].update(Panel(stats_table, title="Stats"))
            
            # Positions section
            positions = await self.portfolio.get_open_positions()
            pos_table = Table(title="Open Positions")
            pos_table.add_column("Item", style="cyan")
            pos_table.add_column("Buy", style="yellow")
            pos_table.add_column("Current", style="green")
            pos_table.add_column("P/L", style="magenta")
            
            for pos in positions[:5]:  # Show top 5
                pl = pos.get('unrealized_profit', 0)
                pl_color = "green" if pl > 0 else "red"
                pos_table.add_row(
                    pos['market_hash_name'][:20],
                    f"${pos['buy_price']:.2f}",
                    f"${pos.get('current_price', pos['buy_price']):.2f}",
                    f"[{pl_color}]${pl:.2f}[/{pl_color}]"
                )
                
            layout["positions"].update(Panel(pos_table, title="Positions"))
            
            # Strategies section
            strategies = await self.strategies.get_active_strategies()
            strat_table = Table(title="Active Strategies")
            strat_table.add_column("Strategy", style="cyan")
            strat_table.add_column("Allocation", style="yellow")
            strat_table.add_column("ROI", style="green")
            
            for strat in strategies:
                roi = strat['performance'].get('roi', 0)
                roi_color = "green" if roi > 0 else "red"
                strat_table.add_row(
                    strat['name'],
                    f"{strat['allocation']:.0%}",
                    f"[{roi_color}]{roi:.1%}[/{roi_color}]"
                )
                
            layout["strategies"].update(Panel(strat_table, title="Strategies"))
            
        except Exception as e:
            logger.error(f"Console update error: {e}")
            
    async def _get_current_stats(self) -> Dict:
        """Get current statistics"""
        portfolio_value = await self.portfolio.get_portfolio_value()
        daily_stats = await self.portfolio.get_performance_stats(days=1)
        
        # Get latency stats
        from ..utils.performance import monitor
        perf_stats = monitor.get_stats()
        
        return {
            'balance': portfolio_value['cash_balance'],
            'daily_profit': daily_stats.get('total_profit', 0),
            'open_positions': portfolio_value['positions_count'],
            'success_rate': daily_stats.get('success_rate', 0),
            'avg_latency': perf_stats.get('avg_latency', 0),
            'total_value': portfolio_value['total_value']
        }
        
    def _generate_dashboard_html(self) -> str:
        """Generate HTML dashboard"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSFloat Auto-Flipper Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
                .container { max-width: 1400px; margin: 0 auto; }
                .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: #2a2a2a; padding: 20px; border-radius: 8px; text-align: center; }
                .stat-value { font-size: 2em; font-weight: bold; color: #4CAF50; }
                .stat-label { color: #999; margin-top: 5px; }
                .chart-container { background: #2a2a2a; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                h1 { text-align: center; color: #4CAF50; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CSFloat Auto-Flipper Dashboard</h1>
                <div class="stats-grid" id="stats"></div>
                <div class="chart-container">
                    <div id="profitChart"></div>
                </div>
                <div class="chart-container">
                    <div id="positionsChart"></div>
                </div>
            </div>
            <script>
                async function updateDashboard() {
                    const stats = await fetch('/api/stats').then(r => r.json());
                    
                    // Update stats
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">$${stats.balance.toFixed(2)}</div>
                            <div class="stat-label">Balance</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">$${stats.daily_profit.toFixed(2)}</div>
                            <div class="stat-label">Daily Profit</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.open_positions}</div>
                            <div class="stat-label">Open Positions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${(stats.success_rate * 100).toFixed(1)}%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                    `;
                    
                    // Update charts
                    // Implement chart updates
                }
                
                // Update every 5 seconds
                updateDashboard();
                setInterval(updateDashboard, 5000);
            </script>
        </body>
        </html>
        """
        
    def record_trade(self, trade_type: str, strategy: str, success: bool):
        """Record trade metrics"""
        status = 'success' if success else 'failed'
        trade_counter.labels(status=status, strategy=strategy).inc()
        
    def record_latency(self, operation: str, latency_ms: float):
        """Record operation latency"""
        latency_histogram.labels(operation=operation).observe(latency_ms)
        
    def record_websocket_message(self, message_type: str):
        """Record WebSocket message"""
        websocket_messages.labels(type=message_type).inc()
        
    def record_snipe_attempt(self, success: bool):
        """Record snipe attempt"""
        result = 'success' if success else 'failed'
        snipe_attempts.labels(result=result).inc()