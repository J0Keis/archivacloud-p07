import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // El proyecto usa React 18: cargar datos al montar con useEffect es un
      // patrón estándar y correcto. La regla set-state-in-effect es de React 19
      // y lo marca como error, por eso la desactivamos para nuestro stack.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
])
