# Обеспечить защиту тайм-аута вызова сервисного интерфейса на основе механизма тайм-аута.

Вообще говоря, при вызове интерфейсов, использующих сервисы, одной из наиболее распространенных проблем является **тайм-аут**. Тайм-аут вызывает нестабильность системы или дрожание системы в сложной распределенной системе. Если произойдет большое количество таймаутов, ресурсы потока будут зависать насмерть, что приведет к значительному снижению пропускной способности или даже к сбою службы.

Когда вы звоните в различные зависимые службы, особенно в крупные компании, вы даже не знаете человека, который разработал услугу, вы не знаете, какой у него технический уровень, и вообще не знаете этого человека.

Питер Штайнер сказал: «[On the Internet, nobody knows you're a dog](https://en.wikipedia.org/wiki/On_the_Internet,_nobody_knows_you%27re_a_dog)», что означает, что на другом конце Интернета вы даже не подозреваете, что там сидит собака.

![220px-Internet_dog.jpg](./images/220px-Internet_dog.jpg)

В особенно сложных распределенных системах, особенно в крупных компаниях с несколькими командами и масштабным сотрудничеством, вы можете не знать, кому принадлежит сервис. Вполне возможно, что приятель, который занимается разработкой сервиса, является даже стажером. Производительность интерфейсов, использующих сервисы, может быть очень нестабильной: иногда 2 мс, иногда 200 мс или даже 2 с.

Если вы не контролируете тайм-аут вызовов различных зависимых сервисных интерфейсов для обеспечения мер безопасности для вашего сервиса, то весьма вероятно, что производительность вашего сервиса будет снижаться из-за различных нежелательных зависимых сервисов. Большое количество вызовов интерфейса выполняется очень медленно, и большое количество потоков зависает. Если изолировать ресурсы, то потоки в пуле потоков будут зависать, но на самом деле мы можем управлять таймаутами и нет необходимости позволять им всем зависать.

## ТаймаутМиллисекунды

В Hystrix мы можем вручную установить продолжительность таймаута. Если время выполнения команды превышает установленную продолжительность, это считается тайм-аутом, а затем команда Hystrix помечается как тайм-аут, и в то же время выполняется резервная логика возврата.

`TimeoutMilliseconds` Значение по умолчанию — 1000, что соответствует 1000 мс.

```java
HystrixCommandProperties.Setter()
    ..withExecutionTimeoutInMilliseconds(int)
```

## Тайм-аут включен

Этот параметр используется для управления включением механизма тайм-аута. Значение по умолчанию — true.

```java
HystrixCommandProperties.Setter()
    .withExecutionTimeoutEnabled(boolean)
```

## Пример демонстрации

В команде мы устанавливаем тайм-аут на 500 мс, а затем устанавливаем время сна на 1 с в методе run(). Когда поступает запрос, он напрямую переходит в режим сна на 1 с, и из-за таймаута выполняется резервная логика.

```java
public class GetProductInfoCommand extends HystrixCommand<ProductInfo> {

    private Long productId;

    private static final HystrixCommandKey KEY = HystrixCommandKey.Factory.asKey("GetProductInfoCommand");

    public GetProductInfoCommand(Long productId) {
        super(Setter.withGroupKey(HystrixCommandGroupKey.Factory.asKey("ProductInfoService"))
                .andCommandKey(KEY)
                .andThreadPoolPropertiesDefaults(HystrixThreadPoolProperties.Setter()
                        .withCoreSize(8)
                        .withMaxQueueSize(10)
                        .withQueueSizeRejectionThreshold(8))
                .andCommandPropertiesDefaults(HystrixCommandProperties.Setter()
                        .withCircuitBreakerEnabled(true)
                        .withCircuitBreakerRequestVolumeThreshold(20)
                        .withCircuitBreakerErrorThresholdPercentage(40)
                        .withCircuitBreakerSleepWindowInMilliseconds(3000)
                        // 设置是否打开超时，默认是true
                        .withExecutionTimeoutEnabled(true)
                        // 设置超时时间，默认1000(ms)
                        .withExecutionTimeoutInMilliseconds(500)
                        .withFallbackIsolationSemaphoreMaxConcurrentRequests(30)));
        this.productId = productId;
    }

    @Override
    protected ProductInfo run() throws Exception {
        System.out.println("调用接口查询商品数据，productId=" + productId);

        // 休眠1s
        TimeUtils.sleep(1);

        String url = "http://localhost:8081/getProductInfo?productId=" + productId;
        String response = HttpClientUtils.sendGetRequest(url);
        System.out.println(response);
        return JSONObject.parseObject(response, ProductInfo.class);
    }

    @Override
    protected ProductInfo getFallback() {
        ProductInfo productInfo = new ProductInfo();
        productInfo.setName("降级商品");
        return productInfo;
    }
}
```

В тестовом классе мы напрямую инициируем запрос.

```java
@SpringBootTest
@RunWith(SpringRunner.class)
public class TimeoutTest {

    @Test
    public void testTimeout() {
        HttpClientUtils.sendGetRequest("http://localhost:8080/getProductInfo?productId=1");
    }
}
```

Как вы можете видеть в результатах, распечатывается информация, связанная с резервным продуктом.

```c
ProductInfo(id=null, name=降级商品, price=null, pictureList=null, specification=null, service=null, color=null, size=null, shopId=null, modifiedTime=null, cityId=null, cityName=null, brandId=null, brandName=null)
{"id": 1, "name": "iphone7手机", "price": 5599, "pictureList":"a.jpg,b.jpg", "specification": "iphone7的规格", "service": "iphone7的售后服务", "color": "红色,白色,黑色", "size": "5.5", "shopId": 1, "modifiedTime": "2017-01-01 12:00:00", "cityId": 1, "brandId": 1}
```
