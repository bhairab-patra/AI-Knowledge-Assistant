const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
const CURRENT_LEVEL = import.meta.env.VITE_LOG_LEVEL || 'info';

const logger = {
  debug: (...args) => LOG_LEVELS[CURRENT_LEVEL] <= 0 && console.debug('[DEBUG]', ...args),
  info: (...args) => LOG_LEVELS[CURRENT_LEVEL] <= 1 && console.info('[INFO]', ...args),
  warn: (...args) => LOG_LEVELS[CURRENT_LEVEL] <= 2 && console.warn('[WARN]', ...args),
  error: (...args) => LOG_LEVELS[CURRENT_LEVEL] <= 3 && console.error('[ERROR]', ...args),
};

export default logger;