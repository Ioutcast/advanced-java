# Исчерпывающее руководство по углублённым знаниям для Java-инженера в интернете

[![stars](https://img.shields.io/github/stars/doocs/advanced-java?color=42b883&logo=github&style=flat-square&logoColor=ffffff)](https://github.com/doocs/advanced-java/stargazers)
[![forks](https://img.shields.io/github/forks/doocs/advanced-java?color=42b883&logo=github&style=flat-square&logoColor=ffffff)](https://github.com/doocs/advanced-java/network/members)
[![license](https://img.shields.io/github/license/doocs/advanced-java?color=42b883&style=flat-square&logo=homeassistantcommunitystore&logoColor=ffffff)](./LICENSE)
[![doocs](https://img.shields.io/badge/org-join%20us-42b883?style=flat-square&logo=homeassistantcommunitystore&logoColor=ffffff)](https://doocs.github.io/#/?id=how-to-join)

Большая часть материалов этого проекта взята у Китайского Шишаня (Zhonghua Shishan), авторские права принадлежат автору. Содержание охватывает такие области, как [высокая параллельность](#архитектура-высокой-параллельности), [распределённые системы](#распределённые-системы), [высокая доступность](#архитектура-высокой-доступности), [микросервисы](#архитектура-микросервисов) и [обработка больших данных](#обработка-больших-данных). Мы систематизировали эти знания для удобства изучения.

Мы также активно обновляем проект по алгоритмам! Если вы готовитесь к алгоритмическим собеседованиям или хотите улучшить свои навыки программирования, ставьте Star проекту [doocs/leetcode](https://github.com/doocs/leetcode).

Перед изучением этого проекта загляните в [Дискуссии](https://github.com/doocs/advanced-java/discussions/9), чтобы узнать, что говорят технические рекрутеры. Приглашаем разработчиков делиться своими идеями и практическим опытом в разделе Discussions. Ставьте Star на [doocs/advanced-java](https://github.com/doocs/advanced-java), чтобы следить за обновлениями.

## Архитектура высокой параллельности

### [Очереди сообщений](/docs/high-concurrency/mq-interview.md)

-   [Зачем нужны очереди сообщений? Каковы их преимущества и недостатки? В чём плюсы и минусы Kafka, ActiveMQ, RabbitMQ, RocketMQ?](/docs/high-concurrency/why-mq.md)
-   [Как обеспечить высокую доступность очереди сообщений?](/docs/high-concurrency/how-to-ensure-high-availability-of-message-queues.md)
-   [Как гарантировать, что сообщение не будет обработано повторно? (Как обеспечить идемпотентность потребления?)](/docs/high-concurrency/how-to-ensure-that-messages-are-not-repeatedly-consumed.md)
-   [Как обеспечить надёжную передачу сообщений? (Как решить проблему потери сообщений?)](/docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md)
-   [Как гарантировать порядок сообщений?](/docs/high-concurrency/how-to-ensure-the-order-of-messages.md)
-   [Как решить проблемы с задержкой, истечением срока действия и переполнением очереди? Что делать, если накопилось несколько миллионов сообщений на несколько часов?](/docs/high-concurrency/mq-time-delay-and-expired-failure.md)
-   [Если бы вас попросили спроектировать очередь сообщений с нуля, как бы вы подошли к архитектуре? Опишите ваши идеи.](/docs/high-concurrency/mq-design.md)

### [Поисковые системы](/docs/high-concurrency/es-introduction.md)

-   [Можете рассказать о принципах распределённой архитектуры Elasticsearch (как ES реализует распределённость)?](/docs/high-concurrency/es-architecture.md)
-   [Как работает запись данных в ES? Как работает поиск? Что такое Lucene под капотом? Знакомы ли с инвертированным индексом?](/docs/high-concurrency/es-write-query-search.md)
-   [Как повысить эффективность поиска в ES при очень больших объёмах данных (миллиарды записей)?](/docs/high-concurrency/es-optimizing-query-performance.md)
-   [Какова архитектура продакшн-кластера ES? Каков примерный объём данных на индекс? Сколько шардов обычно используется на индекс?](/docs/high-concurrency/es-production-cluster.md)

### Кэширование

-   [Как используется кэш в вашем проекте? К каким последствиям может привести неправильное использование кэша?](/docs/high-concurrency/why-cache.md)
-   [В чём разница между Redis и Memcached? Какова потоковая модель Redis? Почему однопоточный Redis эффективнее многопоточного Memcached?](/docs/high-concurrency/redis-single-thread-model.md)
-   [Какие типы данных поддерживает Redis? В каких сценариях какой тип лучше использовать?](/docs/high-concurrency/redis-data-types.md)
-   [Какие стратегии удаления ключей с истекшим сроком действия существуют в Redis? Напишите реализацию LRU вручную?](/docs/high-concurrency/redis-expiration-policies-and-lru.md)
-   [Как обеспечить высокую параллельность и доступность Redis? Можете описать принципы репликации мастер-слейв и механизма Sentinel?](/docs/high-concurrency/how-to-ensure-high-concurrency-and-high-availability-of-redis.md)
-   [Как устроена архитектура мастер-слейв в Redis?](/docs/high-concurrency/redis-master-slave.md)
-   [Как кластер Redis Sentinel обеспечивает высокую доступность?](/docs/high-concurrency/redis-sentinel.md)
-   [Какие механизмы персистентности есть в Redis? В чём плюсы и минусы каждого? Как они реализованы на низком уровне?](/docs/high-concurrency/redis-persistence.md)
-   [Можете объяснить принцип работы кластерного режима Redis? Как выполняется поиск ключа в кластере? Какие алгоритмы распределённого хеширования существуют? Что такое консистентное хеширование? Как динамически добавлять и удалять узлы?](/docs/high-concurrency/redis-cluster.md)
-   [Что такое "лавина", "пробивание" и "пробой" кэша в Redis? Что произойдёт при падении Redis? Как система должна реагировать на такие ситуации? Как бороться с пробиванием кэша?](/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md)
-   [Как обеспечить согласованность данных между кэшем и базой данных при двойной записи?](/docs/high-concurrency/redis-consistence.md)
-   [В чём суть проблемы конкурентного доступа в Redis? Как её решить? Знакомы ли с CAS-подходом в транзакциях Redis?](/docs/high-concurrency/redis-cas.md)
-   [Как разворачивается Redis в продакшн-среде?](/docs/high-concurrency/redis-production-environment.md)
-   [Знакомы ли с процессом перехеширования (rehash) в Redis?](/docs/high-concurrency/redis-rehash.md)

### Шардирование баз данных и таблиц

-   [Зачем нужно шардирование (при проектировании высоконагруженной системы)? Какие middleware для шардирования вы использовали? Их плюсы и минусы? Как вы выполняете вертикальное и горизонтальное шардирование?](/docs/high-concurrency/database-shard.md)
-   [Есть система без шардирования, но в будущем планируется его внедрение. Как спроектировать систему, чтобы переход был плавным?](/docs/high-concurrency/database-shard-method.md)
-   [Как спроектировать схему шардирования, позволяющую динамически расширять и сжимать количество узлов?](/docs/high-concurrency/database-shard-dynamic-expand.md)
-   [Как генерировать глобальные идентификаторы (ID) после шардирования?](/docs/high-concurrency/database-shard-global-id-generate.md)

### Разделение чтения и записи

-   [Как реализовать разделение чтения и записи в MySQL? В чём суть репликации мастер-слейв? Как бороться с задержками синхронизации на слейвах?](/docs/high-concurrency/mysql-read-write-separation.md)

### Системы с высокой параллельностью

-   [Как спроектировать систему с высокой параллельностью?](/docs/high-concurrency/high-concurrency-design.md)

## Распределённые системы

### [Собеседование: шквал вопросов](/docs/distributed-system/distributed-system-interview.md)

### Разделение системы

-   [Зачем разделять систему? Как это делать? Можно ли обойтись без Dubbo после разделения?](/docs/distributed-system/why-dubbo.md)

### Фреймворки для распределённых сервисов

-   [Расскажите о принципе работы Dubbo. Если реестр упадёт, сможет ли общение продолжаться?](/docs/distributed-system/dubbo-operating-principle.md)
-   [Какие протоколы сериализации поддерживает Dubbo? Расскажите о структуре данных Hessian. Что такое Protocol Buffers (PB)? Почему PB самый эффективный?](/docs/distributed-system/dubbo-serialization-protocol.md)
-   [Какие стратегии балансировки нагрузки и отказоустойчивости кластера поддерживает Dubbo? Какие стратегии динамического прокси?](/docs/distributed-system/dubbo-load-balancing.md)
-   [В чём заключается концепция SPI в Dubbo?](/docs/distributed-system/dubbo-spi.md)
-   [Как на основе Dubbo выполнять управление сервисами, снижение нагрузки, повторные попытки при сбоях и тайм-аутах?](/docs/distributed-system/dubbo-service-management.md)
-   [Как спроектировать идемпотентность интерфейса распределённого сервиса (например, чтобы нельзя было дважды списать деньги)?](/docs/distributed-system/distributed-system-idempotency.md)
-   [Как гарантировать порядок выполнения запросов к распределённому сервису?](/docs/distributed-system/distributed-system-request-sequence.md)
-   [Как спроектировать RPC-фреймворк, аналогичный Dubbo?](/docs/distributed-system/dubbo-rpc-design.md)
-   [Что означает "P" в теореме CAP?](/docs/distributed-system/distributed-system-cap.md)

### Распределённые блокировки

-   [Какие сценарии применения есть у Zookeeper?](/docs/distributed-system/zookeeper-application-scenarios.md)
-   [Как спроектировать распределённую блокировку с помощью Redis? А с помощью Zookeeper? Какой из этих подходов эффективнее?](/docs/distributed-system/distributed-lock-redis-vs-zookeeper.md)

### Распределённые транзакции

-   [Знакомы ли с распределёнными транзакциями? Как вы решаете эту проблему? Что делать, если при TCC возникают сетевые проблемы? Как обеспечивается согласованность в XA?](/docs/distributed-system/distributed-transaction.md)

### Распределённые сессии

-   [Как организовать распределённые сессии в кластерной среде?](/docs/distributed-system/distributed-session.md)

## Архитектура высокой доступности

-   [Введение в Hystrix](/docs/high-availability/hystrix-introduction.md)
-   [Архитектура страницы товара в интернет-магазине](/docs/high-availability/e-commerce-website-detail-page-architecture.md)
-   [Изоляция ресурсов через пул потоков Hystrix](/docs/high-availability/hystrix-thread-pool-isolation.md)
-   [Изоляция ресурсов через семафоры Hystrix](/docs/high-availability/hystrix-semphore-isolation.md)
-   [Тонкая настройка стратегий изоляции в Hystrix](/docs/high-availability/hystrix-execution-isolation.md)
-   [Внутренние принципы выполнения Hystrix](/docs/high-availability/hystrix-process.md)
-   [Оптимизация массового запроса данных о товарах с использованием request cache](/docs/high-availability/hystrix-request-cache.md)
-   [Механизм fallback с локальным кэшированием](/docs/high-availability/hystrix-fallback.md)
-   [Принцип работы автоматического выключателя (circuit breaker) в Hystrix](/docs/high-availability/hystrix-circuit-breaker.md)
-   [Изоляция через пул потоков и ограничение запросов в Hystrix](/docs/high-availability/hystrix-thread-pool-current-limiting.md)
-   [Защита от тайм-аутов при вызове сервисов с помощью механизма timeout](/docs/high-availability/hystrix-timeout.md)

### Системы с высокой доступностью

-   Как спроектировать систему с высокой доступностью?

### Лимитирование запросов (Rate Limiting)

-   [Как вы ограничиваете запросы? Что вы используете на практике? Расскажите о конкретной реализации.](/docs/high-concurrency/how-to-limit-current.md)

### Автоматическое отключение (Circuit Breaking)

-   Как выполняется автоматическое отключение?
-   Какие фреймворки для этого существуют? Знаете ли вы принципы их работы?
-   [Как выбрать фреймворк для автоматического отключения: Sentinel или Hystrix?](/docs/high-availability/sentinel-vs-hystrix.md)

### Снижение нагрузки (Fallback / Degradation)

-   Как выполняется снижение нагрузки?

## Архитектура микросервисов

-   [Весь раздел по микросервисам добавлен дополнительно, будет обновляться позже. Приглашаем читателей к участию](https://github.com/doocs/advanced-java)
-   [Описание архитектуры микросервисов](/docs/micro-services/microservices-introduction.md)
-   [Миграция с монолитной архитектуры на микросервисы](/docs/micro-services/migrating-from-a-monolithic-architecture-to-a-microservices-architecture.md)
-   [Управление данными на основе событий в микросервисах](/docs/micro-services/event-driven-data-management-for-microservices.md)
-   [Выбор стратегии развертывания микросервисов](/docs/micro-services/choose-microservice-deployment-strategy.md)
-   [Преимущества и недостатки микросервисной архитектуры](/docs/micro-services/advantages-and-disadvantages-of-microservice.md)

### Микросервисы на Spring Cloud

-   [Что такое микросервисы? Как микросервисы общаются друг с другом?](/docs/micro-services/what's-microservice-how-to-communicate.md)
-   В чём разница между Spring Cloud и Dubbo?
-   Что вы понимаете под Spring Boot и Spring Cloud?
-   Что такое "отключение сервиса" и "снижение нагрузки"?
-   Каковы плюсы и минусы микросервисов? Расскажите о проблемах, с которыми вы сталкивались в проектах.
-   [Какие технологии входят в ваш стек микросервисов?](/docs/micro-services/micro-services-technology-stack.md)
-   [Стратегии управления микросервисами](/docs/micro-services/micro-service-governance.md)
-   В чём разница между Eureka и Zookeeper как реестрами сервисов?
-   [Расскажите об основном процессе работы сервиса обнаружения Eureka.](/docs/micro-services/how-eureka-enable-service-discovery-and-service-registration.md)
-   ......

## Обработка больших данных

-   [Как найти одинаковые URL-адреса среди большого их количества?](/docs/big-data/find-common-urls.md)
-   [Как найти самые частотные слова в большом объёме данных?](/docs/big-data/find-top-100-words.md)
-   [Как найти IP-адрес, с которого было больше всего запросов к Baidu за день?](/docs/big-data/find-top-1-ip.md)
-   [Как найти уникальные целые числа в большом наборе данных?](/docs/big-data/find-no-repeat-number.md)
-   [Как определить, существует ли число в огромном наборе данных?](/docs/big-data/find-a-number-if-exists.md)
-   [Как найти самые популярные поисковые запросы?](/docs/big-data/find-hotest-query-string.md)
-   [Как подсчитать количество различных телефонных номеров?](/docs/big-data/count-different-phone-numbers.md)
-   [Как найти медиану среди 500 миллионов чисел?](/docs/big-data/find-mid-value-in-500-millions.md)
-   [Как отсортировать запросы по частоте?](/docs/big-data/sort-the-query-strings-by-counts.md)
-   [Как найти 500 наибольших чисел?](/docs/big-data/find-rank-top-500-numbers.md)
-   [Расскажите о типовых подходах к решению задачи TopK в больших данных.](/docs/big-data/topk-problems-and-solutions.md)

## Тренд звёзд на GitHub

<a href="https://github.com/doocs/advanced-java/stargazers" target="_blank"><img src="./images/starcharts.svg" alt="Количество звёзд с течением времени" /></a>

Примечание: этот график автоматически обновляется с помощью [actions-starcharts](https://github.com/MaoLongLong/actions-starcharts), автор [@MaoLongLong](https://github.com/maolonglong)

---

## Качественные проекты сообщества Doocs

Сообщество разработчиков Doocs стремится создать полноценную и постоянно развивающуюся экосистему для обучения интернет-разработчиков! Ниже представлены некоторые из наших проектов. Приглашаем разработчиков следить за ними.

| #   | Проект                                                            | Описание                                                                                                                  | Популярность                                                                                                                   |
| --- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1   | [advanced-java](https://github.com/doocs/advanced-java)           | Исчерпывающее руководство по углублённым знаниям для Java-инженера: высокая параллельность, распределённые системы, высокая доступность, микросервисы, большие данные. | ![](https://badgen.net/github/stars/doocs/advanced-java) <br>![](https://badgen.net/github/forks/doocs/advanced-java)           |
| 2   | [leetcode](https://github.com/doocs/leetcode)                     | Решения задач LeetCode, "Предложение меча" (2-е издание), "Золотое собеседование программиста" (6-е издание) на разных языках. | ![](https://badgen.net/github/stars/doocs/leetcode) <br>![](https://badgen.net/github/forks/doocs/leetcode)                     |
| 3   | [source-code-hunter](https://github.com/doocs/source-code-hunter) | Анализ исходных кодов популярных интернет-фреймворков и компонентов.                                                       | ![](https://badgen.net/github/stars/doocs/source-code-hunter) <br>![](https://badgen.net/github/forks/doocs/source-code-hunter) |
| 4   | [jvm](https://github.com/doocs/jvm)                               | Конспекты по внутреннему устройству виртуальной машины Java.                                                               | ![](https://badgen.net/github/stars/doocs/jvm) <br>![](https://badgen.net/github/forks/doocs/jvm)                               |
| 5   | [coding-interview](https://github.com/doocs/coding-interview)     | Сборник задач для собеседований, включая "Предложение меча", "Красота программирования" и др.                             | ![](https://badgen.net/github/stars/doocs/coding-interview) <br>![](https://badgen.net/github/forks/doocs/coding-interview)     |
| 6   | [md](https://github.com/doocs/md)                                 | Лаконичный редактор Markdown для WeChat.                                                                                  | ![](https://badgen.net/github/stars/doocs/md) <br>![](https://badgen.net/github/forks/doocs/md)                                 |
| 7   | [technical-books](https://github.com/doocs/technical-books)       | Список технических книг, заслуживающих внимания.                                                                          | ![](https://badgen.net/github/stars/doocs/technical-books) <br>![](https://badgen.net/github/forks/doocs/technical-books)       |

## Участники

Благодарим всех, кто внёс вклад в [сообщество Doocs](https://github.com/doocs). [Как принять участие в разработке проектов.](https://doocs.github.io/#/?id=how-to-join)

<!-- ALL-CONTRIBUTORS-LIST: START - Do not remove or modify this section -->

<a href="https://opencollective.com/doocs/contributors.svg?width=890&button=true"><img src="https://opencollective.com/doocs/contributors.svg?width=890&button=false" /></a>

<!-- ALL-CONTRIBUTORS-LIST: END -->

## Официальный аккаунт в WeChat

Единственный официальный аккаунт сообщества [Doocs](https://github.com/doocs) — **«Doocs»**. Подписывайтесь, чтобы получать **актуальные технические знания и новости индустрии**. Также можете добавить меня в личные контакты (с пометкой GitHub), чтобы я добавил вас в чат для обсуждений.

<table>
  <tr>
    <td align="center" style="width: 260px;">
      <img src="https://cdn-doocs.oss-cn-shenzhen.aliyuncs.com/gh/doocs/images/qrcode-for-doocs.png" style="width: 400px;"><br>
    </td>
    <td align="center" style="width: 260px;">
      <img src="https://cdn-doocs.oss-cn-shenzhen.aliyuncs.com/gh/doocs/images/qrcode-for-yanglbme.png" style="width: 400px;"><br>
    </td>
  </tr>
</table>

Подпишитесь на «**Doocs**» и ответьте **PDF**, чтобы получить офлайн-версию этого руководства в формате PDF (283 страницы) — учиться ещё удобнее!

<img src="./images/pdf.png" style="width: 600px;"><br>