# Как ограничить рейтинг? Как вы это делаете на работе? Расскажите о конкретной реализации?

## Что такое ограничение скорости?

> Ограничение скорости можно рассматривать как резервный вариант услуги. Ограничение скорости заключается в ограничении входящего и исходящего трафика системы для достижения цели защиты системы. Вообще говоря, пропускную способность системы можно измерить. Чтобы обеспечить стабильную работу системы, после достижения порога, который необходимо ограничить, необходимо ограничить трафик и принять некоторые меры для достижения цели ограничения трафика. Например: отложенная обработка, отказ от обработки или частичный отказ от обработки и т. д.

## метод ограничения скорости

### Счетчик

#### Способ реализации

Контролируйте количество запросов в единицу времени.

```java

import java.util.concurrent.atomic.AtomicInteger;

public class Counter {
    /**
     * 最大访问数量
     */
    private final int limit = 10;
    /**
     * 访问时间差
     */
    private final long timeout = 1000;
    /**
     * 请求时间
     */
    private long time;
    /**
     * 当前计数器
     */
    private AtomicInteger reqCount = new AtomicInteger(0);

    public boolean limit() {
        long now = System.currentTimeMillis();
        if (now < time + timeout) {
            // 单位时间内
            reqCount.addAndGet(1);
            return reqCount.get() <= limit;
        } else {
            // 超出单位时间
            time = now;
            reqCount = new AtomicInteger(0);
            return true;
        }
    }
}

```

Недостатки:

Предположим, что запрос происходит в 00:01, в период с 00:01 по 00:58 запросы не отправляются, все оставшиеся запросы `n-1` отправляются в 00:59 (n — количество запросов на ограничение скорости), а n запросов отправляются в 00:01 следующей минуты, так что запросы `2n - 1` поступают в течение 2 секунд.

Предположим, что количество запросов в минуту равно 60 и в секунду может обрабатываться 1 запрос. Пользователь отправляет 60 запросов в 00:59 и 60 запросов в 01:00. В это время происходит 120 запросов за 2 секунды (60 запросов в секунду), что намного превышает порог количества процессов в секунду.

### Скользящее окно

#### Способ реализации

Скользящее окно представляет собой усовершенствованную версию метода счетчика. Он добавляет единицу измерения детализации времени, делит одну минуту на несколько равных частей (6 частей, каждая часть равна 10 секундам), устанавливает независимый счетчик на каждую часть, а счетчик запросов накапливается на 1 между 00:00-00:09. Чем больше количество аликвот, тем более подробной будет статистика ограничения скорости.

```java
package com.example.demo1.service;

import java.util.Iterator;
import java.util.Random;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.stream.IntStream;

public class TimeWindow {
    private ConcurrentLinkedQueue<Long> queue = new ConcurrentLinkedQueue<Long>();

    /**
     * 间隔秒数
     */
    private int seconds;

    /**
     * 最大限流
     */
    private int max;

    public TimeWindow(int max， int seconds) {
        this.seconds = seconds;
        this.max = max;

        /**
         * 永续线程执行清理queue 任务
         */
        new Thread(() -> {
            while (true) {
                try {
                    // 等待 间隔秒数-1 执行清理操作
                    Thread.sleep((seconds - 1) * 1000L);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                clean();
            }
        }).start();

    }

    public static void main(String[] args) throws Exception {

        final TimeWindow timeWindow = new TimeWindow(10， 1);

        // 测试3个线程
        IntStream.range(0， 3).forEach((i) -> {
            new Thread(() -> {

                while (true) {

                    try {
                        Thread.sleep(new Random().nextInt(20) * 100);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                    timeWindow.take();
                }

            }).start();

        });

    }

    /**
     * 获取令牌，并且添加时间
     */
    public void take() {

        long start = System.currentTimeMillis();
        try {

            int size = sizeOfValid();
            if (size > max) {
                System.err.println("超限");

            }
            synchronized (queue) {
                if (sizeOfValid() > max) {
                    System.err.println("超限");
                    System.err.println("queue中有 " + queue.size() + " 最大数量 " + max);
                }
                this.queue.offer(System.currentTimeMillis());
            }
            System.out.println("queue中有 " + queue.size() + " 最大数量 " + max);

        }

    }

    public int sizeOfValid() {
        Iterator<Long> it = queue.iterator();
        Long ms = System.currentTimeMillis() - seconds * 1000;
        int count = 0;
        while (it.hasNext()) {
            long t = it.next();
            if (t > ms) {
                // 在当前的统计时间范围内
                count++;
            }
        }

        return count;
    }

    /**
     * 清理过期的时间
     */
    public void clean() {
        Long c = System.currentTimeMillis() - seconds * 1000;

        Long tl = null;
        while ((tl = queue.peek()) != null && tl < c) {
            System.out.println("清理数据");
            queue.poll();
        }
    }

}

```

### Дырявое ведро Дырявое ведро

#### Способ реализации

Предусмотрено ведро фиксированной вместимости с подачей и сливом воды. Мы не можем оценить количество и скорость поступающей воды, но мы можем контролировать скорость вытекающей воды.

```java
public class LeakBucket {
    /**
     * 时间
     */
    private long time;
    /**
     * 总量
     */
    private Double total;
    /**
     * 水流出去的速度
     */
    private Double rate;
    /**
     * 当前总量
     */
    private Double nowSize;

    public boolean limit() {
        long now = System.currentTimeMillis();
        nowSize = Math.max(0， (nowSize - (now - time) * rate));
        time = now;
        if ((nowSize + 1) < total) {
            nowSize++;
            return true;
        } else {
            return false;
        }

    }
}
```

### Корзина токенов Корзина токенов

#### Способ реализации

Указывается ведро с фиксированной емкостью, и токены заполняются в ведро с фиксированной скоростью. Когда ведро заполнится, жетоны не будут размещаться дальше. Токен будет удаляться из корзины каждый раз, когда поступает запрос. Если в корзине нет токена, запрос выполнить невозможно.

```java
public class TokenBucket {
    /**
     * 时间
     */
    private long time;
    /**
     * 总量
     */
    private Double total;
    /**
     * token 放入速度
     */
    private Double rate;
    /**
     * 当前总量
     */
    private Double nowSize;

    public boolean limit() {
        long now = System.currentTimeMillis();
        nowSize = Math.min(total， nowSize + (now - time) * rate);
        time = now;
        if (nowSize < 1) {
            // 桶里没有token
            return false;
        } else {
            // 存在token
            nowSize -= 1;
            return true;
        }
    }

}
```

## Использование на работе

### шлюз весеннего облака

— Spring Cloud Gateway по умолчанию использует Redis для ограничения скорости. Обычно я просто модифицирую параметры и использую их «из коробки», а не реализую вышеописанные алгоритмы с нуля.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis-reactive</artifactId>
</dependency>
```

```yaml
spring:
    cloud:
        gateway:
            routes:
                - id: requestratelimiter_route

                  uri: lb://pigx-upms
                  order: 10000
                  predicates:
                      - Path=/admin/**

                  filters:
                      - name: RequestRateLimiter

                        args:
                            redis-rate-limiter.replenishRate: 1 # 令牌桶的容积
                            redis-rate-limiter.burstCapacity: 3 # 流速 每秒
                            key-resolver: '#{@remoteAddrKeyResolver}' #SPEL表达式去的对应的bean

                      - StripPrefix=1
```

```java
@Bean
KeyResolver remoteAddrKeyResolver() {
    return exchange -> Mono.just(exchange.getRequest().getRemoteAddress().getHostName());
}
```

### страж

- Контролируйте трафик каждого URL-адреса посредством конфигурации.

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

```yaml
spring:
    cloud:
        nacos:
            discovery:
                server-addr: localhost:8848
        sentinel:
            transport:
                dashboard: localhost:8080
                port: 8720
            datasource:
                ds:
                    nacos:
                        server-addr: localhost:8848
                        dataId: spring-cloud-sentinel-nacos
                        groupId: DEFAULT_GROUP
                        rule-type: flow
                        namespace: xxxxxxxx
```

- Содержимое конфигурации редактируется на Nacos.

```json
[
    {
        "resource": "/hello",
        "limitApp": "default",
        "grade": 1,
        "count": 1,
        "strategy": 0,
        "controlBehavior": 0,
        "clusterMode": false
    }
]
```

- ресурс: имя ресурса, являющегося целью правила ограничения скорости.
- limitApp: источник вызова, на который нацелено управление потоком. Если это значение по умолчанию, источник вызова не будет различаться.
- Оценка: тип порога ограничения скорости, QPS или режим количества потоков, 0 означает ограничение скорости на основе количества параллелизма, 1 означает управление потоком на основе QPS.
- count: порог ограничения скорости
- стратегия: решение основано на самом ресурсе, других связанных ресурсах (refResource) или записи ссылки.
- controlBehavior: эффект управления потоком (режим прямого отклонения/постановки в очередь/медленного запуска)
-clusterMode: является ли это режимом кластера

### Резюме

> Sentinel и Spring Cloud Gateway являются очень хорошими платформами ограничения скорости, но при моем использовании я не подключил [spring-cloud-alibaba](https://github.com/alibaba/spring-cloud-alibaba) к проекту для использования, поэтому я выберу **spring Cloud Gateway**. Когда соединение будет завершено или подключено к проекту Nacos, использование setinel станет более удобным.
