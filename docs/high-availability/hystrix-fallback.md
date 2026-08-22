# Механизм отката, основанный на локальном кеше

Hystrix вызовет резервный механизм отката в следующих четырех ситуациях:

- Автоматический выключатель разомкнут.
- Пул ресурсов заполнен (пул потоков + очередь/семафор).
- Hystrix вызывает различные интерфейсы или обращается к внешним зависимостям, таким как MySQL, Redis, Zookeeper, Kafka и т. д., и возникают любые отклонения от нормы.
— При доступе к внешним зависимостям время доступа слишком велико, и сообщается об исключении TimeoutException.

## Два самых классических механизма отката

- Чистые данные памяти<br>
    В резервной логике вы можете поддерживать ehcache в памяти как автоматически очищаемый кеш LRU на основе памяти, позволяя помещать данные в кеш. Если во внешней зависимости есть исключение, резервный вариант попытается напрямую получить данные из ehcache.

- Значение по умолчанию<br>
    Fallback В логике возврата вы также можете напрямую вернуть значение по умолчанию.

В `HystrixCommand` резервная логика написана путем реализации интерфейса getFallback(); в то время как в `HystrixObservableCommand` реализован метод резюмеWithFallback().

Теперь мы используем простой каштан, чтобы продемонстрировать, как выполняется откат.

Например, есть такая **сцена**. Теперь у нас есть данные о продукте, содержащие идентификатор бренда. Предположим, что обычная логика следующая: получить данные о продукте, вызвать интерфейс службы бренда на основе идентификатора бренда и получить последнее название бренда BrandName.

Если интерфейс фирменного сервиса зависает, то можно попытаться получить из локальной памяти слегка просроченные данные и обойтись ими в первую очередь.

## Шаг 1. Получите данные из локального кэша

Код для локального получения торговой марки примерно следующий.

```java
/**
 * 品牌名称本地缓存
 *
 */
public class BrandCache {

    private static Map<Long, String> brandMap = new HashMap<>();

    static {
        brandMap.put(1L, "Nike");
    }

    /**
     * brandId 获取 brandName
     *
     * @param brandId 品牌id
     * @return 品牌名
     */
    public static String getBrandName(Long brandId) {
        return brandMap.get(brandId);
    }
```

## Шаг 2. Реализация GetBrandNameCommand

В GetBrandNameCommand обычная логика метода run() заключается в вызове интерфейса службы бренда для получения названия бренда. Если вызов завершается неудачей и сообщается об ошибке, будет вызван резервный механизм возврата.

Здесь мы напрямую моделируем ошибку вызова интерфейса и выбрасываем для нее исключение.

В методе getFallback() это наша запасная логика. Мы напрямую получаем данные о торговой марке из локального кеша.

```java
/**
 * 获取品牌名称的command
 *
 */
public class GetBrandNameCommand extends HystrixCommand<String> {

    private Long brandId;

    public GetBrandNameCommand(Long brandId) {
        super(Setter.withGroupKey(HystrixCommandGroupKey.Factory.asKey("BrandService"))
                .andCommandKey(HystrixCommandKey.Factory.asKey("GetBrandNameCommand"))
                .andCommandPropertiesDefaults(HystrixCommandProperties.Setter()
                        // 设置降级机制最大并发请求数
                        .withFallbackIsolationSemaphoreMaxConcurrentRequests(15)));
        this.brandId = brandId;
    }

    @Override
    protected String run() throws Exception {
        // 这里正常的逻辑应该是去调用一个品牌服务的接口获取名称
        // 如果调用失败，报错了，那么就会去调用fallback降级机制

        // 这里我们直接模拟调用报错，抛出异常
        throw new Exception();
    }

    @Override
    protected String getFallback() {
        return BrandCache.getBrandName(brandId);
    }
}
```

`FallbackIsolationSemaphoreMaxConcurrentRequests` используется для установки максимально допустимого количества одновременных запросов для отката. Значение по умолчанию — 10, что ограничивает скорость с помощью механизма семафоров. Если это максимальное значение превышено, отклоните напрямую.

## Шаг 3: Интерфейс вызова CacheController

В CacheController мы получаем идентификатор бренда через ProductInfo, затем создаем команду GetBrandNameCommand и выполняем ее, чтобы попытаться получить имя бренда. При выполнении здесь будет сообщено об ошибке, поскольку мы выдаем исключение непосредственно в методе run(), а Hystrix вызовет метод getFallback() для выполнения логики возврата.

```java
@Controller
public class CacheController {

    @RequestMapping("/getProductInfo")
    @ResponseBody
    public String getProductInfo(Long productId) {
        HystrixCommand<ProductInfo> getProductInfoCommand = new GetProductInfoCommand(productId);

        ProductInfo productInfo = getProductInfoCommand.execute();
        Long brandId = productInfo.getBrandId();

        HystrixCommand<String> getBrandNameCommand = new GetBrandNameCommand(brandId);

        // 执行会抛异常报错，然后走降级
        String brandName = getBrandNameCommand.execute();
        productInfo.setBrandName(brandName);

        System.out.println(productInfo);
        return "success";
    }
}
```

Демонстрация резервной логики в основном закончена.
