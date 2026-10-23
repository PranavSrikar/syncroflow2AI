import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import './refinement.css';
import { LiveTrafficProvider } from './services/liveTraffic';

createRoot(document.getElementById('root')!).render(<LiveTrafficProvider><App /></LiveTrafficProvider>);
