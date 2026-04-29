"""
face_embedder.py
Genera embeddings faciales usando LBP (Local Binary Patterns) + HOG
sin depender de la librería face_recognition.

El embedding resultante es un vector numpy float32 de dimensión fija
que puede compararse con distancia coseno o euclidiana.

Mejoras de robustez v2:
  - CLAHE en lugar de equalizeHist (iluminación variable)
  - Suavizado Gaussiano antes de LBP (menos sensible a expresiones)
  - Se descarta el 15% superior (zona del cabello)
  - LBP multi-escala (radio 1 y radio 2) para textura más rica
"""

import cv2
import numpy as np


# Dimensión del embedding final
EMBEDDING_DIM = 256


def _lbp_histogram(gray_patch: np.ndarray, num_points: int = 8, radius: int = 1) -> np.ndarray:
    """
    Calcula el histograma LBP de un parche en escala de grises.
    Implementación manual que NO requiere scikit-image.
    """
    h, w = gray_patch.shape
    lbp = np.zeros((h, w), dtype=np.uint8)

    for bit, (dy, dx) in enumerate([
        (-radius, 0), (-radius, radius), (0, radius), (radius, radius),
        (radius, 0), (radius, -radius), (0, -radius), (-radius, -radius)
    ]):
        shifted = np.zeros_like(gray_patch)
        # Recorte de origen y destino
        sy = max(dy, 0); ey = h + min(dy, 0)
        sx = max(dx, 0); ex = w + min(dx, 0)
        dy_neg = max(-dy, 0); dy_pos = h - max(dy, 0)
        dx_neg = max(-dx, 0); dx_pos = w - max(dx, 0)
        shifted[dy_neg:dy_pos, dx_neg:dx_pos] = gray_patch[sy:ey, sx:ex]
        lbp |= ((shifted >= gray_patch).astype(np.uint8) << bit)

    hist, _ = np.histogram(lbp.ravel(), bins=32, range=(0, 256))
    return hist.astype(np.float32)


def _hog_simple(gray_patch: np.ndarray, cell_size: int = 16) -> np.ndarray:
    """
    HOG simplificado: gradientes en celdas de cell_size x cell_size,
    histograma de 8 orientaciones por celda.
    """
    resized = cv2.resize(gray_patch, (64, 64))
    gx = cv2.Sobel(resized, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(resized, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2 + gy**2)
    angle = np.arctan2(gy, gx) * (180.0 / np.pi) % 180.0

    n_cells_y = 64 // cell_size
    n_cells_x = 64 // cell_size
    n_bins = 8
    hog_feat = []
    for cy in range(n_cells_y):
        for cx in range(n_cells_x):
            cell_mag = mag[cy*cell_size:(cy+1)*cell_size, cx*cell_size:(cx+1)*cell_size]
            cell_ang = angle[cy*cell_size:(cy+1)*cell_size, cx*cell_size:(cx+1)*cell_size]
            hist, _ = np.histogram(cell_ang.ravel(), bins=n_bins, range=(0, 180),
                                   weights=cell_mag.ravel())
            hog_feat.append(hist)
    return np.concatenate(hog_feat).astype(np.float32)


def compute_face_embedding(face_bgr: np.ndarray) -> np.ndarray:
    """
    Dado un recorte de cara (BGR), retorna un embedding normalizado
    de dimensión EMBEDDING_DIM.

    Args:
        face_bgr: Imagen BGR del recorte de cara (cualquier tamaño).

    Returns:
        np.ndarray float32 de forma (EMBEDDING_DIM,), normalizado a norma 1.
        Retorna None si el recorte es inválido.
    """
    if face_bgr is None or face_bgr.size == 0:
        return None

    try:
        face_bgr = cv2.resize(face_bgr, (128, 128))
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)

        # ── CLAHE: robustez ante iluminación variable ─────────────────────────
        # Mejor que equalizeHist porque adapta el contraste por zonas locales,
        # reduciendo el impacto de sombras o luz directa en la cara.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # ── Suavizado Gaussiano ───────────────────────────────────────────────
        # Reduce la sensibilidad a cambios de textura fina causados por
        # expresiones faciales (muecas, caras raras) sin borrar la estructura.
        gray_smooth = cv2.GaussianBlur(gray, (3, 3), 0.8)

        # ── Excluir zona del cabello (top 15%) ───────────────────────────────
        # El cabello cambia entre intentos (peinado distinto); ignorar esa
        # franja hace el embedding más invariante al peinado.
        h_img = gray_smooth.shape[0]
        hair_cut = int(h_img * 0.15)
        face_core = gray_smooth[hair_cut:, :]   # región ojos → barbilla

        # ── LBP multi-escala ─────────────────────────────────────────────────
        # Radio 1 (textura fina): sensible a detalles pequeños de la piel.
        lbp_r1 = _lbp_histogram(face_core, num_points=8, radius=1)   # 32-dim
        # Radio 2 (textura media): captura contornos de ojos, nariz y boca,
        # que son más estables que los detalles finos al hacer expresiones.
        lbp_r2 = _lbp_histogram(face_core, num_points=8, radius=2)   # 32-dim

        # ── HOG: gradientes de forma ──────────────────────────────────────────
        # Captura la estructura geométrica facial global; más estable que LBP
        # ante pequeñas variaciones de expresión.
        hog_feat = _hog_simple(gray_smooth, cell_size=16)             # 128-dim

        # ── Intensidades medias por bloque ────────────────────────────────────
        # Información de bajo nivel sobre la distribución de brillo en la cara.
        small = cv2.resize(face_core, (8, 8)).astype(np.float32).ravel()  # 64-dim

        # 32 + 32 + 128 + 64 = 256 dims == EMBEDDING_DIM exacto
        embedding = np.concatenate([lbp_r1, lbp_r2, hog_feat, small])

        # Rellenar o truncar hasta EMBEDDING_DIM (seguridad)
        if embedding.shape[0] < EMBEDDING_DIM:
            embedding = np.pad(embedding, (0, EMBEDDING_DIM - embedding.shape[0]))
        else:
            embedding = embedding[:EMBEDDING_DIM]

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)
    except Exception as e:
        print(f"[FaceEmbedder] Error generando embedding: {e}")
        return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Similitud coseno entre dos vectores (mayor = más parecido, máx 1.0)."""
    if a is None or b is None:
        return 0.0
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Distancia euclidiana entre dos vectores (menor = más parecido)."""
    if a is None or b is None:
        return float('inf')
    # Asegurar misma dimensión
    min_len = min(len(a), len(b))
    return float(np.linalg.norm(a[:min_len] - b[:min_len]))
