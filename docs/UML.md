# Архитектурная диаграмма проекта (UML / Mermaid)

Диаграмма иллюстрирует взаимодействие между клиентом, FastAPI бэкендом, базой данных PostgreSQL и трекером Keitaro API.

```mermaid
flowchart TD
    subgraph Client["Клиентский уровень (Frontend SPA)"]
        UI["Web UI: HTML5 + TailwindCSS"]
        JS["Client Logic: app.js"]
        UI <--> JS
    end

    subgraph Backend["FastAPI Backend (Application Core)"]
        RouterCampaigns["api/router/campaigns.py<br/>(Роутер управления кампаниями)"]
        RouterDicts["api/router/dictionaries.py<br/>(Справочники: домены, офферы)"]
        
        CreatorService["services/creator_service.py<br/>(Создание кампании с 2 потоками)"]
        EditorService["services/editor_service.py<br/>(Редактирование офферов и долей)"]
        
        KeitaroClient["integrations/keitaro.py<br/>(Сессионный клиент Keitaro API)"]
        
        DBEngine["core/psql.py & crud/campaign.py<br/>(Async SQLAlchemy Engine)"]
    end

    subgraph Database["Хранилище PostgreSQL"]
        T_Camp[("Таблица: campaigns")]
        T_Offers[("Таблица: campaign_offers")]
        T_Camp --- T_Offers
    end

    subgraph KeitaroTracker["Внешний трекер Keitaro (tlgk.host)"]
        K_Auth["/admin/?object=auth.login"]
        K_Campaigns["/admin/?object=campaigns.create"]
        K_Streams["/admin/?object=streams.create / update"]
        K_Dicts["/admin/?object=offers, domains, groups"]
    end

    JS -->|HTTP GET/POST/DELETE| RouterCampaigns
    JS -->|HTTP GET| RouterDicts
    
    RouterCampaigns --> CreatorService
    RouterCampaigns --> EditorService
    RouterDicts --> KeitaroClient
    
    CreatorService --> KeitaroClient
    EditorService --> KeitaroClient
    
    CreatorService -.->|Сохранение копии| DBEngine
    DBEngine --> Database
    
    KeitaroClient -->|Session Auth| K_Auth
    KeitaroClient -->|Создание кампании| K_Campaigns
    KeitaroClient -->|Управление потоками| K_Streams
    KeitaroClient -->|Получение справочников| K_Dicts
```

## Пояснения к диаграмме компонентов

1. **Client (Web SPA)**:
   - Вкладка **Создаватор кампаний**: форма ввода параметров, валидация двухбуквенного гео-кода и ID оффера, быстрый выбор из выпадающего списка.
   - Вкладка **Редактор существующей кампании**: селектор кампаний, просмотр потока Google-фильтрации, интерактивная таблица офферов целевого потока с кнопками удаления и формой добавления.

2. **Backend Services**:
   - `services/creator_service.py`: отвечает за генерацию безопасного alias, создание базовой кампании и двух потоков (Google-редирект с фильтром страны + целевой поток офферов).
   - `services/editor_service.py`: инкапсулирует логику поиска потока с офферами, добавления/удаления ID оффера и автоматического пересчета весов (`share`).

3. **Database (PostgreSQL & Alembic)**:
   - `campaigns`: хранит локальный аудит созданных кампаний.
   - `campaign_offers`: хранит историю и конфигурацию привязанных офферов.

4. **Keitaro Tracker Integration**:
   - Автоматическая сессионная аутентификация в Keitaro (`auth.login`).
   - Использование преднастроенного домена (ID `1813`), группы (ID `9799`) и источника трафика (ID `836`).
