import { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function JobForm({ onJobCreated }) {
  const [text, setText] = useState('');
  const [strategy, setStrategy] = useState('round_robin');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      toast.error('Por favor, ingrese algún texto ');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await axios.post(`${API}/jobs`, {
        text: text,
        balancing_strategy: strategy
      });
      
      toast.success(`Trabajo creado: ${response.data.job_id}`);
      setText('');
      onJobCreated();
    } catch (error) {
      toast.error('Error al crear el trabajo');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setText(event.target.result);
      toast.success('Archivo cargado');
    };
    reader.readAsText(file);
  };

  const loadSampleText = () => {
    const sample = `Yo oí que en Perú, Benín, Afganistán, Venezuela y Suecia, recorren varios kilómetros para
    lograr conseguir bebidas, comida, huertos, juegos, drogas enérgicas, whiskys, cuadernos para xerografía y
    fotos de pingüinos, qué extraño.`.repeat(5);
    setText(sample); // It's called Panagram
    toast.success('Texto de ejemplo cargado');
  };

  return (
    <div className="job-form-container" data-testid="job-form">
      <div className="card">
        <h2 className="card-title">Crear Trabajo de MapReduce</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="text-input">Entrada de Texto</label>
            <textarea
              id="text-input"
              data-testid="text-input"
              className="form-textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ingrese el texto que desee analizar o cargue un archivo..."
              rows={8}
            />
            <div className="text-info">
              {text.length} caracteres
            </div>
          </div>

          <div className="form-actions">
            <label className="file-upload-btn" data-testid="file-upload-label">
              <input
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                data-testid="file-upload-input"
              />
              Seleccionar Archivo
            </label>
            <button
              type="button"
              onClick={loadSampleText}
              className="secondary-btn"
              data-testid="load-sample-btn"
            >
              Cargar Ejemplo
            </button>
          </div>

          <div className="form-group">
            <label htmlFor="strategy-select">Estrategia de Balanceo</label>
            <select
              id="strategy-select"
              data-testid="strategy-select"
              className="form-select"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="round_robin">Round Robin</option>
              <option value="least_loaded">Least Loaded</option>
            </select>
          </div>

          <button
            type="submit"
            className="submit-btn"
            disabled={isSubmitting}
            data-testid="submit-job-btn"
          >
            {isSubmitting ? 'Creando...' : 'Iniciar Trabajo'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default JobForm;
