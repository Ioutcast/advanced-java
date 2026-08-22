#Углубленное понимание принципа работы автоматического выключателя Hystrix

### Государственный автомат

Автоматический выключатель Hystrix имеет три состояния: «закрыто», «разомкнуто» и «полуразомкнуто». Отношения трансформации между тремя состояниями следующие:

![image-20191104211642271](./images/hystrix-circuit-breaker-state-machine.png)

1. `Closed` Автоматический выключатель замкнут: запрос на вызов нижестоящего устройства проходит нормально.
1. `Open` Разомкните автоматический выключатель: заблокируйте вызовы нижестоящих служб и напрямую используйте резервную логику.
1. `Half-Open` Автоматический выключатель наполовину разомкнут: [SleepWindowInMilliseconds](#circuitBreaker.sleepWindowInMilliseconds)

### [Enabled](https://github.com/Netflix/Hystrix/wiki/Configuration#circuitbreakerenabled)

```java
HystrixCommandProperties.Setter()
    .withCircuitBreakerEnabled(boolean)
```

Контролируйте, работает ли автоматический выключатель, включая отслеживание состояния работоспособности зависимых сервисных вызовов, а также разрешать ли срабатывание автоматического выключателя при слишком большом количестве исключений. Значение по умолчанию `true`.

### [circuitBreaker.requestVolumeThreshold](https://github.com/Netflix/Hystrix/wiki/Configuration#circuitbreakerrequestvolumethreshold)

```java
HystrixCommandProperties.Setter()
    .withCircuitBreakerRequestVolumeThreshold(int)
```

Указывает минимальное количество запросов, прежде чем может сработать разрыв цепи в статистическом скользящем окне времени (этот параметр также очень важен, обсуждается ниже). Значение по умолчанию — 20. **Трафик, проходящий через автоматический выключатель Hystrix, может вызвать разрыв цепи только после того, как он превысит определенный порог. **Например, требуется, чтобы количество трафика, проходящего через автоматический выключатель, достигало 20 в течение 10 секунд, но на самом деле через автоматический выключатель проходит 19 запросов. Даже если все 19 запросов потерпят неудачу, не будет принято решение о разрыве цепи.

### [circuitBreaker.errorThresholdPercentage](https://github.com/Netflix/Hystrix/wiki/Configuration#circuitBreaker.errorThresholdPercentage)

```java
HystrixCommandProperties.Setter()
    .withCircuitBreakerErrorThresholdPercentage(int)
```

Указывает на ненормальную пропорцию перед срабатыванием разрыва цепи. Значение по умолчанию — 50(%).

#### [circuitBreaker.sleepWindowInMilliseconds](https://github.com/Netflix/Hystrix/wiki/Configuration#circuitbreakersleepwindowinmilliseconds)

```java
HystrixCommandProperties.Setter()
    .withCircuitBreakerSleepWindowInMilliseconds(int)
```

Состояние автоматического выключателя меняется с «Включено» на «Разомкнуто». В течение следующего времени `SleepWindowInMilliseconds` все запросы, проходящие через автоматический выключатель, будут отключены. Внутренняя служба не будет вызываться, а резервный механизм будет использоваться напрямую. Значение по умолчанию — 5000 (мс).

По истечении заданного времени автоматический выключатель перейдет в полуоткрытое и замкнутое состояние `Half-Open`. Попробуйте пропустить запрос через автоматический выключатель, чтобы проверить, можно ли его вызвать нормально. В случае успешного вызова он автоматически восстанавливается и выключатель переводится в состояние ВКЛ.

### [ForceOpen](https://github.com/Netflix/Hystrix/wiki/Configuration#circuitbreakerforceopen)

```java
HystrixCommandProperties.Setter()
    .withCircuitBreakerForceOpen(boolean)
```

Если установлено значение true, автоматический выключатель принудительно размыкается напрямую, что эквивалентно ручному отключению цепи и ручному возврату в аварийный режим. Значение по умолчанию — `false`.

### [ForceClosed](https://github.com/Netflix/Hystrix/wiki/Configuration#circuitbreakerforceclosed)

```java
HystrixCommandProperties.Setter()
    .withCircuitBreakerForceClosed(boolean)
```

Если установлено значение true, автоматический выключатель принудительно замыкается напрямую, что эквивалентно остановке автоматического выключателя вручную и обновлению вручную. Значение по умолчанию — `false`.

### Статистика метрик

В тесном сотрудничестве с автоматическим выключателем Hystrix имеется еще один важный компонент — **Метрики**. Наиболее важными параметрами статистики являются скользящее окно ([metrics.rollingStats.timeInMilliseconds](https://github.com/Netflix/Hystrix/wiki/Configuration#metricsrollingstatstimeinmilliseconds)) и сегмент ([metrics.rollingStats.numBuckets](https://github.com/Netflix/Hystrix/wiki/Configuration#metricsrollingstatsnumbuckets)). Здесь [сообщение в блоге](https://zhenbianshu.github.io/2018/09/hystrix_configuration_analysis.html) цитируется для объяснения скользящего окна (значение по умолчанию — 10000 мс):

> Пассажир сидел на сиденье у окна движущегося поезда. По обеим сторонам дороги, по которой шел поезд, росли высокие тополи. Когда поезд двинулся вперед, тополя на обочине быстро проскользнули мимо окна. Мы используем каждое дерево для обозначения запроса, а движение поезда — для обозначения течения времени. Тогда окно в поезде представляет собой типичное раздвижное окно, а тополя, которые пассажиры могут видеть через окно, — это данные, которые хочет собрать Hystrix.

Hystrix не учитывает время прохождения запроса, а делит все скользящее окно на numBuckets и считает каждый раз, когда он проходит. **По прошествии определенного времени будет принято решение о том, следует ли включать автоматический выключатель или нет. См. пример ниже. **

## Пример демонстрации

### Параметры конфигурации HystrixCommand

Настройте параметры, связанные с автоматическим выключателем Setter, в GetProductInfoCommand.

- В скользящем окне не менее 20 запросов могут вызвать разрыв цепи.
- Разрыв цепи срабатывает, когда коэффициент ненормальности достигает 40%.
— В течение 3000 мс после разрыва цепи все запросы будут отклонены и будет использован резервный вариант напрямую, без вызова метода run(). Через 3000 мс он переходит в полуоткрытое состояние.

В методе run() мы определяем, равен ли ProductId -1. Если да, создайте исключение напрямую. Написанный таким образом, мы можем передать ProductId=-1 во время тестирования позже, чтобы имитировать исключения при выполнении службы.

В логике резервного копирования мы можем просто вернуть резервный продукт непосредственно к нему.

```java
public class GetProductInfoCommand extends HystrixCommand<ProductInfo> {

    private Long productId;

    private static final HystrixCommandKey KEY = HystrixCommandKey.Factory.asKey("GetProductInfoCommand");

    public GetProductInfoCommand(Long productId) {
        super(Setter.withGroupKey(HystrixCommandGroupKey.Factory.asKey("ProductInfoService"))
                .andCommandKey(KEY)
                .andCommandPropertiesDefaults(HystrixCommandProperties.Setter()
                        // 是否允许断路器工作
                        .withCircuitBreakerEnabled(true)
                        // 滑动窗口中，最少有多少个请求，才可能触发断路
                        .withCircuitBreakerRequestVolumeThreshold(20)
                        // 异常比例达到多少，才触发断路，默认50%
                        .withCircuitBreakerErrorThresholdPercentage(40)
                        // 断路后多少时间内直接reject请求，之后进入half-open状态，默认5000ms
                        .withCircuitBreakerSleepWindowInMilliseconds(3000)));
        this.productId = productId;
    }

    @Override
    protected ProductInfo run() throws Exception {
        System.out.println("调用接口查询商品数据，productId=" + productId);

        if (productId == -1L) {
            throw new Exception();
        }

        String url = "http://localhost:8081/getProductInfo?productId=" + productId;
        String response = HttpClientUtils.sendGetRequest(url);
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

### Класс испытания на разрыв цепи

В нашем тестовом классе для первых 30 запросов передается ProductId=-1, затем он приостанавливается на 3 секунды, а для следующих 70 запросов передается ProductId=1.

```java
@SpringBootTest
@RunWith(SpringRunner.class)
public class CircuitBreakerTest {

    @Test
    public void testCircuitBreaker() {
        String baseURL = "http://localhost:8080/getProductInfo?productId=";

        for (int i = 0; i < 30; ++i) {
            // 传入-1，会抛出异常，然后走降级逻辑
            HttpClientUtils.sendGetRequest(baseURL + "-1");
        }

        TimeUtils.sleep(3);
        System.out.println("After sleeping...");

        for (int i = 31; i < 100; ++i) {
            // 传入1，走服务正常调用
            HttpClientUtils.sendGetRequest(baseURL + "1");
        }
    }
}
```

### Результаты теста

По результатам тестирования мы можем наглядно увидеть весь процесс отключения и восстановления системы.

```java
调用接口查询商品数据，productId=-1
ProductInfo(id=null, name=降级商品, price=null, pictureList=null, specification=null, service=null, color=null, size=null, shopId=null, modifiedTime=null, cityId=null, cityName=null, brandId=null, brandName=null)
// ...
// 这里重复打印了 20 次上面的结果


ProductInfo(id=null, name=降级商品, price=null, pictureList=null, specification=null, service=null, color=null, size=null, shopId=null, modifiedTime=null, cityId=null, cityName=null, brandId=null, brandName=null)
// ...
// 这里重复打印了 8 次上面的结果


// 休眠 3s 后
调用接口查询商品数据，productId=1
ProductInfo(id=1, name=iphone7手机, price=5599.0, pictureList=a.jpg,b.jpg, specification=iphone7的规格, service=iphone7的售后服务, color=红色,白色,黑色, size=5.5, shopId=1, modifiedTime=2017-01-01 12:00:00, cityId=1, cityName=null, brandId=1, brandName=null)
// ...
// 这里重复打印了 69 次上面的结果
```

Для первых 30 запросов переданный нами идентификатор продукта был равен -1, поэтому во время выполнения службы будет выдано исключение. Мы устанавливаем минимум 20 запросов через автоматический выключатель и запускаем автоматический выключатель, когда коэффициент исключений превышает 40%. Таким образом, был выполнен 21 вызов интерфейса, каждый раз вызывалось исключение и выполнялся возврат к резервному варианту. После 21 раза автоматический выключатель был разомкнут.

Метод `run()` не будет выполняться для следующих 9 запросов, и следующая информация не будет напечатана.

```c
调用接口查询商品数据，productId=-1
```

Вместо этого перейдите непосредственно к резервной логике и вызовите getFallback() для выполнения.

После сна в течение 3 секунд мы передали ProductId, равный 1, в следующих 70 запросах. Поскольку мы установили его ранее, автоматический выключатель изменится на `half-open` через 3000 мс. Таким образом, Hystrix попытается выполнить запрос, и в случае успеха автоматический выключатель будет замкнут, и все последующие запросы можно будет вызывать в обычном режиме.

### Справочный контент

1. [Hystrix issue 1459](https://github.com/Netflix/Hystrix/issues/1459)
1. [Hystrix Metrics](https://github.com/Netflix/Hystrix/wiki/Configuration#metrics)
