# Реализовать изоляцию ресурсов на основе технологии пула потоков Hystrix.

[Предыдущая лекция](./e-commerce-website-detail-page-architecture.md) упомянул, что если кеш станет недействительным, начиная с Nginx, Nginx напрямую вызовет службу продукта через службу кеша, чтобы получить последние данные о продукте (мы обсудим это на основе проекта электронной коммерции). Возможна задержка вызова и исчерпание ресурсов службы кэширования. Здесь давайте поговорим о том, как добиться изоляции ресурсов с помощью технологии пула потоков Hystrix.

Изоляция ресурсов означает, что если вы хотите изолировать все вызовы определенной зависимой службы в одном пуле ресурсов и не использовать другие ресурсы, это называется изоляцией ресурсов. Даже для такого зависимого сервиса, как сервис продукта, количество одновременных вызовов достигло 1000, но пулу потоков сервиса продукта выделено только 10 потоков, и для выполнения будет использоваться максимум только эти 10 потоков. Все ресурсы потоков в Tomcat не будут исчерпаны из-за задержек при вызове служб продукта.

Hystrix реализует изоляцию ресурсов, фактически предоставляя абстракцию под названием Command. Это также самая базовая технология изоляции ресурсов Hystrix.

## Используйте HystrixCommand для получения одного фрагмента данных

Мы инкапсулируем операцию вызова служб продукта в HystrixCommand и ограничиваем ключ, например `GetProductInfoCommandGroup` ниже. Здесь мы можем просто думать об этом как о пуле потоков. Каждый раз при вызове службы продукта будут использоваться только ресурсы из пула потоков, а другие ресурсы потоков использоваться не будут.

```java
public class GetProductInfoCommand extends HystrixCommand<ProductInfo> {

    private Long productId;

    public GetProductInfoCommand(Long productId) {
        super(HystrixCommandGroupKey.Factory.asKey("GetProductInfoCommandGroup"));
        this.productId = productId;
    }

    @Override
    protected ProductInfo run() {
        String url = "http://localhost:8081/getProductInfo?productId=" + productId;
        // 调用商品服务接口
        String response = HttpClientUtils.sendGetRequest(url);
        return JSONObject.parseObject(response, ProductInfo.class);
    }
}
```

В интерфейсе службы кэширования мы создаем команду на основе идентификатора продукта и выполняем ее для получения данных о продукте.

```java
@RequestMapping("/getProductInfo")
@ResponseBody
public String getProductInfo(Long productId) {
    HystrixCommand<ProductInfo> getProductInfoCommand = new GetProductInfoCommand(productId);

    // 通过command执行，获取最新商品数据
    ProductInfo productInfo = getProductInfoCommand.execute();
    System.out.println(productInfo);
    return "success";
}
```

Выше выполняется метод Execute(), который на самом деле является синхронным. Вы также можете вызвать метод очереди() для этой команды. Он просто помещает команду в очередь ожидания в пуле потоков и немедленно возвращается, чтобы получить объект Future. Вы можете продолжить заниматься другими делами позже, а затем через некоторое время вызвать метод get() для Future, чтобы получить данные. Это асинхронно.

## Используйте HystrixObservableCommand для пакетного получения данных

Пока данные о продукте получены, все привязано к одному и тому же пулу потоков. Мы выполняем его через поток HystrixObservableCommand, и в этом потоке информация о продукте для нескольких идентификаторов продукта извлекается обратно в пакетном режиме.

```java
public class GetProductInfosCommand extends HystrixObservableCommand<ProductInfo> {

    private String[] productIds;

    public GetProductInfosCommand(String[] productIds) {
        // 还是绑定在同一个线程池
        super(HystrixCommandGroupKey.Factory.asKey("GetProductInfoGroup"));
        this.productIds = productIds;
    }

    @Override
    protected Observable<ProductInfo> construct() {
        return Observable.unsafeCreate((Observable.OnSubscribe<ProductInfo>) subscriber -> {

            for (String productId : productIds) {
                // 批量获取商品数据
                String url = "http://localhost:8081/getProductInfo?productId=" + productId;
                String response = HttpClientUtils.sendGetRequest(url);
                ProductInfo productInfo = JSONObject.parseObject(response, ProductInfo.class);
                subscriber.onNext(productInfo);
            }
            subscriber.onCompleted();

        }).subscribeOn(Schedulers.io());
    }
}
```

В интерфейсе службы кэширования в соответствии с переданным списком идентификаторов, например строкой идентификатора, разделенной символом `,`, с помощью вышеуказанной команды HystrixObservableCommand выполняются некоторые методы API Hystrix для получения всех данных о продукте.

```java
public String getProductInfos(String productIds) {
    String[] productIdArray = productIds.split(",");
    HystrixObservableCommand<ProductInfo> getProductInfosCommand = new GetProductInfosCommand(productIdArray);
    Observable<ProductInfo> observable = getProductInfosCommand.observe();

    observable.subscribe(new Observer<ProductInfo>() {
        @Override
        public void onCompleted() {
            System.out.println("获取完了所有的商品数据");
        }

        @Override
        public void onError(Throwable e) {
            e.printStackTrace();
        }

        /**
         * 获取完一条数据，就回调一次这个方法
         * @param productInfo
         */
        @Override
        public void onNext(ProductInfo productInfo) {
            System.out.println(productInfo);
        }
    });
    return "success";
}
```

Давайте вернемся назад и посмотрим, как технология пула потоков Hystrix реализует изоляцию ресурсов.

![hystrix-thread-pool-isolation](./images/hystrix-thread-pool-isolation.png)

Начиная с Nginx, кеш стал недействительным, поэтому Nginx использует службу кэша для вызова сервисов продукта. Размер потока службы кэша по умолчанию равен 10, и существует не более 10 потоков для вызова интерфейса службы продукта. Даже если интерфейс службы продукта выйдет из строя, на пути к вызову интерфейса службы продукта будет зависать максимум 10 потоков. Другие потоки службы кэша Tomcat по-прежнему можно использовать для вызова других служб и выполнения других задач.
