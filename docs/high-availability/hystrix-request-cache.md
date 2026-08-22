# Оптимизация интерфейса запроса данных о пакетном продукте на основе технологии кэширования запросов.

Третий шаг из 8 шагов при выполнении команды Hystrix — проверить, кэширован ли кэш запросов.

Прежде всего, существует концепция под названием «Контекст запроса». Вообще говоря, если в веб-приложении мы используем Hystrix, мы будем применять контекст запроса к каждому запросу в фильтре. Другими словами, каждый запрос — это запрос контекста. Затем в контексте этого запроса мы выполним еще N кодов и вызовем еще N зависимых сервисов. Некоторые зависимые службы могут вызываться несколько раз.

В контексте запроса, если имеется несколько команд, параметры одинаковы, вызываемый интерфейс также тот же, и результаты можно считать одинаковыми. Затем в это время мы можем кэшировать результат, возвращаемый первым выполнением команды, в памяти, а затем все последующие вызовы этой зависимости в этом контексте запроса будут извлекать кэшированные результаты из памяти.

Преимущество в этом случае состоит в том, что нет необходимости выполнять одну и ту же команду несколько раз в контексте запроса, что позволяет избежать повторного выполнения сетевых запросов и повышает производительность всего запроса.

Дай мне каштан. Например, в контексте запроса мы запрашиваем получение данных с идентификатором продукта, равным 1. Если его нет в первом кеше, то данные будут получены из службы продукта, будет возвращен последний результат данных, и данные будут кэшированы в памяти. Если в последующем контексте того же запроса будет другой запрос на получение данных с идентификатором продукта, равным 1, просто извлеките его непосредственно из кеша.

![hystrix-request-cache](./images/hystrix-request-cache.png)

И HystrixCommand, и HystrixObservableCommand могут указать ключ кэша, после чего Hystrix автоматически его кэширует. Затем в том же контексте запроса, если к нему снова будет осуществлен доступ, к кешу будет доступен прямой доступ.

Далее давайте посмотрим, как использовать технологию кэширования запросов на основе конкретного **бизнес-сценария**. Конечно, следующий код — это только базовая демонстрация.

Теперь предположим, что мы хотим создать интерфейс для пакетного запроса данных о продукте. При этом мы используем HystrixCommand для одновременного запроса данных нескольких идентификаторов продуктов в пакетах. Но здесь есть проблема. Если локальный кеш Nginx выходит из строя и пакет кешей получается повторно, а переданные идентификаторы продуктов не дедуплицируются, например `productIds=1,1,1,2,2`, то можно сказать, что идентификатор продукта повторяется. Если мы будем следовать нашей предыдущей бизнес-логике, мы можем запросить продукт с ProductId=1 три раза и продукт с ProductId=2 дважды.

Мы можем использовать кеш запросов для оптимизации интерфейса для пакетного запроса данных о продукте. То есть один запрос является контекстом запроса. Один и тот же запрос продукта выполняется только один раз, а остальные дубликаты попадают в кеш запросов.

## Реализуем контекстный фильтр запроса Hystrix и регистрируем его

Определите класс HystrixRequestContextFilter и реализуйте интерфейс Filter.

```java
/**
 * Hystrix 请求上下文过滤器
 */
public class HystrixRequestContextFilter implements Filter {

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {

    }

    @Override
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) {
        HystrixRequestContext context = HystrixRequestContext.initializeContext();
        try {
            filterChain.doFilter(servletRequest, servletResponse);
        } catch (IOException | ServletException e) {
            e.printStackTrace();
        } finally {
            context.shutdown();
        }
    }

    @Override
    public void destroy() {

    }
}
```

Затем зарегистрируйте объект фильтра в приложении SpringBoot.

```java
@SpringBootApplication
public class EshopApplication {

    public static void main(String[] args) {
        SpringApplication.run(EshopApplication.class, args);
    }

    @Bean
    public FilterRegistrationBean filterRegistrationBean() {
        FilterRegistrationBean filterRegistrationBean = new FilterRegistrationBean(new HystrixRequestContextFilter());
        filterRegistrationBean.addUrlPatterns("/*");
        return filterRegistrationBean;
    }
}
```

## команда переопределяет метод getCacheKey()

В GetProductInfoCommand переопределите метод getCacheKey(), чтобы результат каждого запроса помещался в контекст запроса Hystrix. Следующий запрос данных для того же ProductId будет получен непосредственно из кеша без повторного вызова метода run().

```java
public class GetProductInfoCommand extends HystrixCommand<ProductInfo> {

    private Long productId;

    private static final HystrixCommandKey KEY = HystrixCommandKey.Factory.asKey("GetProductInfoCommand");

    public GetProductInfoCommand(Long productId) {
        super(Setter.withGroupKey(HystrixCommandGroupKey.Factory.asKey("ProductInfoService"))
                .andCommandKey(KEY));
        this.productId = productId;
    }

    @Override
    protected ProductInfo run() {
        String url = "http://localhost:8081/getProductInfo?productId=" + productId;
        String response = HttpClientUtils.sendGetRequest(url);
        System.out.println("调用接口查询商品数据，productId=" + productId);
        return JSONObject.parseObject(response, ProductInfo.class);
    }

    /**
     * 每次请求的结果，都会放在Hystrix绑定的请求上下文上
     *
     * @return cacheKey 缓存key
     */
    @Override
    public String getCacheKey() {
        return "product_info_" + productId;
    }

    /**
     * 将某个商品id的缓存清空
     *
     * @param productId 商品id
     */
    public static void flushCache(Long productId) {
        HystrixRequestCache.getInstance(KEY,
                HystrixConcurrencyStrategyDefault.getInstance()).clear("product_info_" + productId);
    }
}
```

Здесь написан методlushCache() для нашей разработки, позволяющий вручную удалить кеш.

## Контроллер вызывает команду для запроса информации о продукте

В контексте веб-запроса передается список идентификаторов продуктов для запроса информации о нескольких продуктах. Для каждого ProductId создается команда.

Если список идентификаторов не дедуплицирован, дубликаты идентификаторов будут кэшироваться непосредственно во время второго запроса.

```java
@Controller
public class CacheController {

    /**
     * 一次性批量查询多条商品数据的请求
     *
     * @param productIds 以,分隔的商品id列表
     * @return 响应状态
     */
    @RequestMapping("/getProductInfos")
    @ResponseBody
    public String getProductInfos(String productIds) {
        for (String productId : productIds.split(",")) {
            // 对每个productId，都创建一个command
            GetProductInfoCommand getProductInfoCommand = new GetProductInfoCommand(Long.valueOf(productId));
            ProductInfo productInfo = getProductInfoCommand.execute();
            System.out.println("是否是从缓存中取的结果：" + getProductInfoCommand.isResponseFromCache());
        }

        return "success";
    }
}
```

## Инициировать запрос

Вызовите интерфейс, чтобы запросить информацию о нескольких продуктах.

```
http://localhost:8080/getProductInfos?productIds=1,1,1,2,2,5
```

В консоли мы видим следующие результаты.

```
调用接口查询商品数据，productId=1
是否是从缓存中取的结果：false
是否是从缓存中取的结果：true
是否是从缓存中取的结果：true
调用接口查询商品数据，productId=2
是否是从缓存中取的结果：false
是否是从缓存中取的结果：true
调用接口查询商品数据，productId=5
是否是从缓存中取的结果：false
```

При первом запросе данных ProductId=1 интерфейс будет вызываться для запроса вместо получения результатов из кеша. При последующем запросе ProductId=1 кэш будет извлечен напрямую. В этом случае эффективность будет существенно выше.

## Удалить кеш

Пишем UpdateProductInfoCommand. После обновления информации о продукте мы вручную вызываем функциюlushCache(), которую мы написали ранее, чтобы вручную удалить кеш.

```java
public class UpdateProductInfoCommand extends HystrixCommand<Boolean> {

    private Long productId;

    public UpdateProductInfoCommand(Long productId) {
        super(HystrixCommandGroupKey.Factory.asKey("UpdateProductInfoGroup"));
        this.productId = productId;
    }

    @Override
    protected Boolean run() throws Exception {
        // 这里执行一次商品信息的更新
        // ...

        // 然后清空缓存
        GetProductInfoCommand.flushCache(productId);
        return true;
    }
}
```

Таким образом, будущие запросы на запрос этого продукта будут впервые выполнять вызов интерфейса для запроса последней информации о продукте.
