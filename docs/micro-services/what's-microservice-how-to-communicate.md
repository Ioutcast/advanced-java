# Что такое микросервисы? Как микросервисы взаимодействуют независимо друг от друга?

## Что такое микросервисы

- Архитектура микросервисов представляет собой распределенную систему, которая разделена на различные сервисные единицы в зависимости от бизнеса для устранения недостатков производительности единой системы.
— Микросервисы — это архитектурный стиль, в котором большое программное приложение состоит из нескольких сервисных модулей. Сервисные блоки в системе могут быть развернуты независимо, и каждый сервисный блок слабо связан.

> Происхождение концепции микросервисов: [Microservices](https://martinfowler.com/articles/microservices.html)

## Как микросервисы взаимодействуют независимо друг от друга

### Синхронизация

#### HTTP-протокол REST

Запрос REST — это наиболее часто используемый метод связи в микросервисах, основанный на протоколе HTTP\HTTPS. Характеристики RESTFUL:

1. Каждый URI представляет ресурс.
2. Клиент использует GET, POST, PUT и DELETE для управления ресурсами сервера: GET используется для получения ресурсов, POST используется для создания новых ресурсов (его также можно использовать для обновления ресурсов), PUT используется для обновления ресурсов, а DELETE используется для удаления ресурсов.
3. Манипулируйте ресурсами, манипулируя их представлением.
4. Ресурс выражен в XML или HTML.
5. Взаимодействие между клиентом и сервером не имеет состояния между запросами. Каждый запрос от клиента к серверу должен содержать информацию, необходимую для понимания запроса.

Например, поставщик услуг предоставляет следующий интерфейс:

```java
@RestController
@RequestMapping("/communication")
public class RestControllerDemo {
    @GetMapping("/hello")
    public String s() {
        return "hello";
    }
}
```

Другой службе необходимо вызвать этот интерфейс, а вызывающей стороне достаточно отправить запрос в соответствии с документом API, чтобы получить возвращаемый результат.

```java
@RestController
@RequestMapping("/demo")
public class RestDemo{
    @Autowired
    RestTemplate restTemplate;

    @GetMapping("/hello2")
    public String s2() {
        String forObject = restTemplate.getForObject("http://localhost:9013/communication/hello", String.class);
        return forObject;
    }
}
```

Таким образом может быть достигнута связь между службами.

#### TCP-протокол RPC

RPC (Удаленный вызов процедур) Удаленный вызов процедуры. Простым пониманием является то, что один узел запрашивает услуги, предоставляемые другим узлом. Его рабочий процесс выглядит следующим образом:

1. Выполните оператор вызова клиента и передайте параметры.
2. Вызовите локальную систему для отправки сетевых сообщений.
3. Отправьте сообщение на удаленный хост.
4. Сервер получает сообщение и параметры.
5. Выполнить удаленный процесс (сервис) согласно вызывающему запросу и параметрам.
6. После завершения процесса выполнения результат возвращается в дескриптор сервера.
7. Дескриптор сервера возвращает результат и вызывает системную сетевую службу удаленного хоста для отправки результата.
8. Сообщение отправляется обратно на локальный хост.
9. Дескриптор клиента получает сообщения от сетевой службы локального хоста.
10. Клиент получает данные результата, возвращенные вызывающим оператором.

Приведите пример.

Сначала вам нужен сервер:

```java
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.lang.reflect.Method;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * RPC 服务端用来注册远程方法的接口和实现类
 */
public class RPCServer {
    private static ExecutorService executor = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

    private static final ConcurrentHashMap<String, Class> serviceRegister = new ConcurrentHashMap<>();

    /**
     * 注册方法
     * @param service
     * @param impl
     */
    public void register(Class service, Class impl) {
        serviceRegister.put(service.getSimpleName(), impl);
    }

    /**
     * 启动方法
     * @param port
     */
    public void start(int port) {
        ServerSocket socket = null;
        try {
            socket = new ServerSocket();
            socket.bind(new InetSocketAddress(port));
            System.out.println("服务启动");
            System.out.println(serviceRegister);
            while (true) {
                executor.execute(new Task(socket.accept()));
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (socket != null) {
                try {
                    socket.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    private static class Task implements Runnable {
        Socket client = null;

        public Task(Socket client) {
            this.client = client;
        }

        @Override
        public void run() {
            ObjectInputStream input = null;
            ObjectOutputStream output = null;
            try {
                input = new ObjectInputStream(client.getInputStream());
                // 按照顺序读取对方写过来的内容
                String serviceName = input.readUTF();
                String methodName = input.readUTF();
                Class<?>[] parameterTypes = (Class<?>[]) input.readObject();
                Object[] arguments = (Object[]) input.readObject();
                Class serviceClass = serviceRegister.get(serviceName);
                if (serviceClass == null) {
                    throw new ClassNotFoundException(serviceName + " 没有找到!");
                }
                Method method = serviceClass.getMethod(methodName, parameterTypes);
                Object result = method.invoke(serviceClass.newInstance(), arguments);

                output = new ObjectOutputStream(client.getOutputStream());
                output.writeObject(result);
            } catch (Exception e) {
                e.printStackTrace();

            } finally {
                try {
                    // 这里就不写 output!=null才关闭这个逻辑了
                    output.close();
                    input.close();
                    client.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }

            }
        }
    }

}

```

Во-вторых, вам нужен клиент:

```java
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.net.InetSocketAddress;
import java.net.Socket;

/**
 * RPC 客户端
 */
public class RPCclient<T> {
    /**
     * 通过动态代理将参数发送过去到 RPCServer ,RPCserver 返回结果这个方法处理成为正确的实体
     */
    public static <T> T getRemoteProxyObj(final Class<T> service, final InetSocketAddress addr) {

        return (T) Proxy.newProxyInstance(service.getClassLoader(), new Class<?>[]{service}, new InvocationHandler() {
            @Override
            public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {

                Socket socket = null;
                ObjectOutputStream out = null;
                ObjectInputStream input = null;
                try {
                    socket = new Socket();
                    socket.connect(addr);

                    // 将实体类,参数,发送给远程调用方
                    out = new ObjectOutputStream(socket.getOutputStream());
                    out.writeUTF(service.getSimpleName());
                    out.writeUTF(method.getName());
                    out.writeObject(method.getParameterTypes());
                    out.writeObject(args);

                    input = new ObjectInputStream(socket.getInputStream());
                    return input.readObject();
                } catch (Exception e) {
                    e.printStackTrace();
                } finally {
                    out.close();
                    input.close();
                    socket.close();
                }
                return null;
            }
        });

    }

}

```

Вот еще один удаленный метод тестирования.

```java
public interface Tinterface {
    String send(String msg);
}

public class TinterfaceImpl implements Tinterface {
    @Override
    public String send(String msg) {
        return "send message " + msg;
    }
}

```

Тестовый код выглядит следующим образом:

```java
import java.net.InetSocketAddress;


public class RunTest {
    public static void main(String[] args) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                RPCServer rpcServer = new RPCServer();
                rpcServer.register(Tinterface.class, TinterfaceImpl.class);
                rpcServer.start(10000);
            }
        }).start();
        Tinterface tinterface = RPCclient.getRemoteProxyObj(Tinterface.class, new InetSocketAddress("localhost", 10000));
        System.out.println(tinterface.send("rpc 测试用例"));

    }
}

```

Выход `send message rpc 测试用例` .

### Асинхронный

#### Промежуточное программное обеспечение для сообщений

К распространенным промежуточным ПО для сообщений относятся Kafka, ActiveMQ, RabbitMQ и RocketMQ, а к распространенным протоколам относятся AMQP, MQTTP, STOMP и XMPP. Очередь сообщений здесь расширяться не будет. Подробную информацию о том, как его использовать, можно найти на официальном сайте.
