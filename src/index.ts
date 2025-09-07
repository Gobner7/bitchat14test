import { Command } from 'commander';
import { loadConfig } from './config.js';
import { logger } from './logger.js';
import { runTraderLoop } from './trader.js';

const program = new Command();
program
  .name('csfloat-flipper')
  .description('Automated CSFloat flipper bot')
  .version('1.0.0');

program
  .command('trade')
  .description('Run the trading loop')
  .action(async () => {
    const cfg = loadConfig();
    logger.info({ cfg }, 'Configuration loaded');
    await runTraderLoop();
  });

program.parseAsync(process.argv);

