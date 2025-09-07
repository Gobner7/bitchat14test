// @ts-check
import js from '@eslint/js';
import pluginImport from 'eslint-plugin-import';
import prettier from 'eslint-config-prettier';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';

export default [
  {
    ignores: ['dist/**', 'node_modules/**'],
  },
  js.configs.recommended,
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: false,
      },
      globals: {
        process: 'readonly',
        setTimeout: 'readonly',
        URLSearchParams: 'readonly',
        document: 'readonly',
      },
    },
    plugins: { import: pluginImport, '@typescript-eslint': tsPlugin },
    rules: {
      'import/no-unresolved': 'off',
      'no-empty': 'off',
    },
  },
  prettier,
];

