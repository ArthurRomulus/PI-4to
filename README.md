<h1 align="center">Sistema Biométrico de Control de Acceso con Reconocimiento Facial</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Activo-success">
  <img src="https://img.shields.io/badge/Python-3.10-blue">
  <img src="https://img.shields.io/badge/OpenCV-4.x-green">
  <img src="https://img.shields.io/badge/Hardware-Raspberry%20Pi%205-red">
  <img src="https://img.shields.io/badge/License-Academic-lightgrey">
</p>

<hr>

<h2>Descripción del Proyecto</h2>

<p>
Sistema de autenticación biométrica basado en reconocimiento facial implementado en una Raspberry Pi 5.
El sistema está diseñado para mejorar la seguridad en el acceso principal universitario mediante procesamiento local (Edge Computing),
evitando la dependencia de servidores externos y reduciendo la latencia.
</p>

<hr>

<h2>Funcionamiento del Sistema</h2>

<ol>
  <li>Captura de imagen mediante cámara USB.</li>
  <li>Detección facial usando OpenCV.</li>
  <li>Extracción de características mediante algoritmo LBPH.</li>
  <li>Comparación con base de datos local.</li>
  <li>Validación y activación de relé para apertura de puerta.</li>
</ol>

<hr>

<h2>Arquitectura del Sistema</h2>

<pre>
 Cámara USB
      │
      ▼
 Raspberry Pi 5
      │
      ├──  OpenCV (Detección)
      ├──  LBPH (Reconocimiento)
      ├──  phyton/SQL (Base de datos)
      └──  GPIO (Control de relé)
      │
      ▼
 Cerradura electrónica
</pre>

<hr>

<h2> Tecnologías Utilizadas</h2>

<ul>
  <li>Python 3.10</li>
  <li>OpenCV</li>
  <li>Algoritmo LBPH</li>
  <li>SQLite</li>
  <li>GPIO</li>
  <li>Raspberry Pi OS</li>
</ul>

<hr>

<h2>Características Principales</h2>

<ul>
  <li>✔ Procesamiento local (Edge Computing)</li>
  <li>✔ Baja latencia (&lt; 1 segundo)</li>
  <li>✔ Registro automático de accesos</li>
  <li>✔ Reducción de suplantación de identidad</li>
  <li>✔ Integración hardware-software</li>
</ul>

<hr>

<h2>Comparación con Sistema Tradicional</h2>

<table border="1" cellpadding="8" cellspacing="0">
  <tr>
    <th>Sistema Tradicional</th>
    <th>Sistema Biométrico</th>
  </tr>
  <tr>
    <td>Credenciales físicas</td>
    <td>Identidad biométrica</td>
  </tr>
  <tr>
    <td>Posible préstamo</td>
    <td>Intransferible</td>
  </tr>
  <tr>
    <td>Registro manual</td>
    <td>Registro digital automático</td>
  </tr>
  <tr>
    <td>Dependencia humana</td>
    <td>Automatización total</td>
  </tr>
</table>

<hr>

<h2>Galería del Proyecto</h2>

<img src="images/sistema.jpg" width="600"><br><br>
<img src="images/reconocimiento.jpg" width="600"><br><br>
<img src="images/rele.jpg" width="600">

<hr>

<h2>Resultados Esperados</h2>

<ul>
  <li> Reducción de accesos no autorizados</li>
  <li> Optimización del flujo de entrada</li>
  <li> Trazabilidad completa de usuarios</li>
  <li> Mayor seguridad institucional</li>
</ul>

<hr>

<h2> Mejoras Futuras</h2>

<ul>
  <li>Detección de vida (Anti-Spoofing)</li>
  <li>Dashboard web de monitoreo</li>
  <li>Encriptación avanzada de vectores biométricos</li>
  <li>mejorar la Seguridad del sistema</li>
</ul>

<hr>

<h2>Autor</h2>

<p>
Proyecto académico enfocado en sistemas biométricos embebidos para seguridad universitaria.<br>
  Dimas Rolon Aram Sebastian<br>
  Erick yonan Ibarra heredia<br> 
  Arturo GArzon Parra<br>
  quiroz paez<br>
  ernesto Hernandez Cebrera<br> 
</p>

<p align="center">
  <strong>© 2026 - Proyecto de Ingeniería</strong>
</p>
