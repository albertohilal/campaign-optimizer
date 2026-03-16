# Diagnóstico Inicial – Campaign Optimizer

## 1. Contexto
Este documento registra el estado inicial del proyecto Campaign Optimizer y de la campaña de Google Ads antes de implementar optimizaciones. Su objetivo es dejar una línea base técnica y funcional que permita comparar el sistema actual con las mejoras que se incorporen en etapas posteriores.

## 2. Estado actual del proyecto
Actualmente el proyecto se encuentra con la base de Phase 1 implementada y operativa. La aplicación cuenta con una base FastAPI funcionando, una configuración centralizada para variables de entorno y una inicialización de base de datos SQLite lista para desarrollo local. También se encuentra creado el modelo AnalysisReport para persistir reportes de análisis, existe un wrapper de Google Ads con soporte de mock mode para trabajar sin credenciales reales en desarrollo, el endpoint de health responde correctamente y la cobertura de tests es todavía mínima, enfocada en validar el estado básico de la API.

## 3. Arquitectura actual
La arquitectura actual sigue una estructura simple y clara basada en el flujo routes → services → persistence.

La capa de routes concentra los endpoints HTTP y expone la interfaz pública de la API. Su responsabilidad es recibir requests, validar entradas mediante schemas y delegar el trabajo de negocio.

La capa de services contiene la lógica aplicada a integraciones y casos de uso. Aquí se ubica actualmente el servicio de Google Ads, que encapsula la conexión con la API externa y el uso de datos simulados cuando corresponde.

La capa de persistence agrupa la configuración de base de datos, la sesión de SQLAlchemy y los modelos ORM. Esta capa se encarga de la persistencia del estado y deja preparada la evolución futura hacia almacenamiento de reportes y resultados analíticos.

## 4. Estado de la integración con Google Ads
La integración con Google Ads ya tiene una base implementada a través del servicio google_ads_client. Este servicio permite encapsular la inicialización del cliente oficial, manejar errores de manera controlada y ofrecer un modo de trabajo desacoplado del entorno real.

El mock mode permite continuar el desarrollo sin credenciales reales, devolviendo datos simulados cuando el entorno está en desarrollo y no se configuraron secretos de Google Ads. Esto evita bloquear el avance del proyecto y facilita pruebas funcionales tempranas.

Actualmente get_campaigns ya está implementado y puede devolver campañas reales o simuladas según el contexto de ejecución. En cambio, get_campaign_metrics y get_search_terms todavía no están implementados para modo real y permanecen como pendientes de Phase 2.

## 5. Problemas o huecos detectados
Se detectan varios huecos relevantes antes de avanzar con nuevas funcionalidades. El README actual no refleja el estado final esperado del proyecto y requiere consolidación como documentación operativa real. La cobertura de tests sigue siendo limitada y todavía no valida componentes críticos como configuración, root endpoint o integración mock de Google Ads. Los endpoints de campañas aún no están expuestos a través de la API, por lo que el wrapper existente no puede consumirse desde rutas públicas. La conversión entre schemas estructurados y el JSON persistido en AnalysisReport todavía no está implementada de punta a punta. Además, la capa de métricas y términos de búsqueda sigue pendiente para integración real con Google Ads.

## 6. Hoja de ruta de implementación
El orden sugerido para la implementación es el siguiente:

1. endpoint /campaigns
2. metrics_service
3. endpoint /analysis/snapshot
4. analyzer
5. recommendations
6. generación de reportes

## 7. Nota final
Este documento representa la línea base técnica desde la cual se evaluarán las mejoras futuras del sistema. Cualquier optimización posterior deberá contrastarse contra este estado inicial para medir impacto, cobertura funcional y evolución de la arquitectura.