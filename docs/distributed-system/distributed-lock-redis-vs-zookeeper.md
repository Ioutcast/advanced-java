# Redis и Zookeeper реализуют распределенную блокировку

## Вопрос на собеседовании

Каковы общие способы реализации распределенной блокировки? Как спроектировать распределенную блокировку с помощью Redis? Можно ли использовать zk для разработки распределенной блокировки? Какой из этих двух методов реализации распределенной блокировки более эффективен?

## Что хочет знать интервьюер

На самом деле общий вопрос задается так. Сначала спросим вас о zk, а затем перейдем к некоторым вопросам, связанным с zk, например, о распределенной блокировке. Потому что при разработке распределенных систем сценарии использования распределенной блокировки все еще очень распространены.

## Анализ вопросов на собеседовании

### Распределенная блокировка Redis

Официально называемый алгоритмом `RedLock`, это алгоритм распределенной блокировки, официально поддерживаемый Redis.

У этой распределенной блокировки есть три важных соображения:

- Взаимное исключение (только один клиент может получить блокировку)
- Нет тупика
— Отказоустойчивость (пока большинство узлов Redis создают эту блокировку)

#### Redis Самая распространенная распределенная блокировка.

Первый и наиболее распространенный метод реализации — использовать `SET key value [EX seconds] [PX milliseconds] NX` для создания ключа в Redis, чтобы он был заблокирован. Среди них:

- `NX`: указывает, что настройка будет успешной только в том случае, если `key` не существует. Если этот `key` существует в Redis в данный момент, настройка завершится неудачно и будет возвращен `nil`.
- `EX seconds`: установите время истечения `key` с точностью до второго уровня. Это означает, что блокировка будет автоматически снята через `seconds` секунд. Если кто-то другой обнаружит, что он уже существует при его создании, он не сможет его заблокировать.
- `PX milliseconds`: также устанавливается время истечения `key` с точностью до миллисекунды.

Например, выполните следующую команду:

```r
SET resource_name my_random_value PX 30000 NX
```

Снятие блокировки означает удаление ключа, но обычно вы можете использовать сценарий `lua`, чтобы удалить его, а затем удалить его, определив, что значение то же самое:

```lua
-- 删除锁的时候，找到 key 对应的 value，跟自己传过去的 value 做比较，如果是一样的才删除。
if redis.call("get",KEYS[1]) == ARGV[1] then
    return redis.call("del",KEYS[1])
else
    return 0
end
```

Зачем использовать случайное значение `random_value`? Потому что, если клиент получает блокировку, но блокирует ее на долгое время для завершения выполнения, например, более 30 секунд, блокировка может быть автоматически снята в это время. В это время блокировку могли получить другие клиенты. Если вы сразу удалите ключ, возникнут проблемы, поэтому вам придется использовать случайное значение плюс приведенный выше сценарий `lua`, чтобы снять блокировку.

Но это определенно невозможно. Потому что если это обычный единичный экземпляр Redis, то это единая точка отказа. Или обычная репликация Redis master-slave, затем асинхронная репликация Redis master-slave. Если главный узел зависает (ключ пропал), ключ не синхронизирован с подчиненным узлом. В это время подчиненный узел переключается на главный узел, а другие могут установить ключ и получить блокировку.

#### Алгоритм RedLock

В этом сценарии предполагается наличие кластера Redis с пятью главными экземплярами Redis. Затем выполните следующие действия для получения блокировки:

1. Получите текущую метку времени, единица измерения — миллисекунды;
2. Аналогично предыдущему, попробуйте создать блокировки на каждом мастер-узле по очереди, с коротким таймаутом, обычно в десятки миллисекунд (таймаут, используемый клиентом для получения блокировки, меньше, чем общее время автоматического снятия блокировки. Например, если время автоматического снятия блокировки составляет 10 секунд, то таймаут может находиться в диапазоне `5~50` миллисекунд);
3. Попробуйте установить блокировку на **большинстве узлов**, например, для 5 узлов требуется 3 узла `n / 2 + 1`;
4. Клиент рассчитывает время на установку блокировки. Если время установления блокировки меньше таймаута, она считается успешной;
5. Если установка блокировки не удалась, последовательно удалите ранее установленные блокировки;
6. Пока кто-то другой создает распределенную блокировку, вам придется постоянно опрашивать ее, пытаясь получить блокировку.

![redis-redlock](./images/redis-redlock.png)

[официальный представитель Redis](https://redis.io/) описывает два вышеупомянутых метода реализации распределенной блокировки на основе Redis. Подробное описание можно найти по адресу: https://redis.io/topics/distlock.

### распределенная блокировка zk

распределенную блокировку zk, по сути, можно сделать относительно просто, то есть узел пытается создать временный znode, и если создание проходит успешно, он получает блокировку; в это время другие клиенты не смогут создать блокировку и смогут только зарегистрировать прослушиватель для мониторинга блокировки. Снятие блокировки означает удаление znode. После освобождения клиент будет уведомлен, а затем ожидающий клиент сможет снова заблокировать его.

```java
/**
 * ZooKeeperSession
 */
public class ZooKeeperSession {

    private static CountDownLatch connectedSemaphore = new CountDownLatch(1);

    private ZooKeeper zookeeper;
    private CountDownLatch latch;

    public ZooKeeperSession() {
        try {
            this.zookeeper = new ZooKeeper("192.168.31.187:2181,192.168.31.19:2181,192.168.31.227:2181", 50000, new ZooKeeperWatcher());
            try {
                connectedSemaphore.await();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }

            System.out.println("ZooKeeper session established......");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 获取分布式锁
     *
     * @param productId
     */
    public Boolean acquireDistributedLock(Long productId) {
        String path = "/product-lock-" + productId;

        try {
            zookeeper.create(path, "".getBytes(), Ids.OPEN_ACL_UNSAFE, CreateMode.EPHEMERAL);
            return true;
        } catch (Exception e) {
            while (true) {
                try {
                    // 相当于是给node注册一个监听器，去看看这个监听器是否存在
                    Stat stat = zk.exists(path, true);

                    if (stat != null) {
                        this.latch = new CountDownLatch(1);
                        this.latch.await(waitTime, TimeUnit.MILLISECONDS);
                        this.latch = null;
                    }
                    zookeeper.create(path, "".getBytes(), Ids.OPEN_ACL_UNSAFE, CreateMode.EPHEMERAL);
                    return true;
                } catch (Exception ee) {
                    continue;
                }
            }

        }
        return true;
    }

    /**
     * 释放掉一个分布式锁
     *
     * @param productId
     */
    public void releaseDistributedLock(Long productId) {
        String path = "/product-lock-" + productId;
        try {
            zookeeper.delete(path, -1);
            System.out.println("release the lock for product[id=" + productId + "]......");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 建立 zk session 的 watcher
     */
    private class ZooKeeperWatcher implements Watcher {

        public void process(WatchedEvent event) {
            System.out.println("Receive watched event: " + event.getState());

            if (KeeperState.SyncConnected == event.getState()) {
                connectedSemaphore.countDown();
            }

            if (this.latch != null) {
                this.latch.countDown();
            }
        }

    }

    /**
     * 封装单例的静态内部类
     */
    private static class Singleton {

        private static ZooKeeperSession instance;

        static {
            instance = new ZooKeeperSession();
        }

        public static ZooKeeperSession getInstance() {
            return instance;
        }

    }

    /**
     * 获取单例
     *
     * @return
     */
    public static ZooKeeperSession getInstance() {
        return Singleton.getInstance();
    }

    /**
     * 初始化单例的便捷方法
     */
    public static void init() {
        getInstance();
    }

}
```

Вы также можете использовать другой способ создания временных узлов последовательности:

Если есть блокировка, за которую конкурируют несколько человек, несколько человек встанут в очередь, и первый человек, получивший блокировку, выполнит, а затем снимет блокировку; все, кто стоит за ними, будут слушать узел, созданный человеком, стоящим перед ними. Как только кто-то снимет блокировку, ZooKeeper уведомит людей, стоящих за ними. После уведомления все будет в порядке, они получат блокировку и смогут выполнить код.

```java
public class ZooKeeperDistributedLock implements Watcher {

    private ZooKeeper zk;
    private String locksRoot = "/locks";
    private String productId;
    private String waitNode;
    private String lockNode;
    private CountDownLatch latch;
    private CountDownLatch connectedLatch = new CountDownLatch(1);
    private int sessionTimeout = 30000;

    public ZooKeeperDistributedLock(String productId) {
        this.productId = productId;
        try {
            String address = "192.168.31.187:2181,192.168.31.19:2181,192.168.31.227:2181";
            zk = new ZooKeeper(address, sessionTimeout, this);
            connectedLatch.await();
        } catch (IOException e) {
            throw new LockException(e);
        } catch (KeeperException e) {
            throw new LockException(e);
        } catch (InterruptedException e) {
            throw new LockException(e);
        }
    }

    public void process(WatchedEvent event) {
        if (event.getState() == KeeperState.SyncConnected) {
            connectedLatch.countDown();
            return;
        }

        if (this.latch != null) {
            this.latch.countDown();
        }
    }

    public void acquireDistributedLock() {
        try {
            if (this.tryLock()) {
                return;
            } else {
                waitForLock(waitNode, sessionTimeout);
            }
        } catch (KeeperException e) {
            throw new LockException(e);
        } catch (InterruptedException e) {
            throw new LockException(e);
        }
    }

    public boolean tryLock() {
        try {
            // 传入进去的locksRoot + “/” + productId
            // 假设productId代表了一个商品id，比如说1
            // locksRoot = locks
            // /locks/10000000000，/locks/10000000001，/locks/10000000002
            lockNode = zk.create(locksRoot + "/" + productId, new byte[0], ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.EPHEMERAL_SEQUENTIAL);

            // 看看刚创建的节点是不是最小的节点
            // locks：10000000000，10000000001，10000000002
            List<String> locks = zk.getChildren(locksRoot, false);
            Collections.sort(locks);

            if (lockNode.equals(locksRoot + "/" + locks.get(0))) {
                // 如果是最小的节点,则表示取得锁
                return true;
            }

            // 如果不是最小的节点，找到比自己小1的节点
            int previousLockIndex = -1;
            for (int i = 0; i < locks.size(); i++) {
                if (lockNode.equals(locksRoot + "/" +locks.get(i))){
                    previousLockIndex = i - 1;
                    break;
                }
            }

            this.waitNode = locks.get(previousLockIndex);
        } catch (KeeperException e) {
            throw new LockException(e);
        } catch (InterruptedException e) {
            throw new LockException(e);
        }
        return false;
    }

    private boolean waitForLock(String waitNode, long waitTime) throws InterruptedException, KeeperException {
        Stat stat = zk.exists(locksRoot + "/" + waitNode, true);
        if (stat != null) {
            this.latch = new CountDownLatch(1);
            this.latch.await(waitTime, TimeUnit.MILLISECONDS);
            this.latch = null;
        }
        return true;
    }

    public void unlock() {
        try {
            // 删除/locks/10000000000节点
            // 删除/locks/10000000001节点
            System.out.println("unlock " + lockNode);
            zk.delete(lockNode, -1);
            lockNode = null;
            zk.close();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (KeeperException e) {
            e.printStackTrace();
        }
    }

    public class LockException extends RuntimeException {
        private static final long serialVersionUID = 1L;

        public LockException(String e) {
            super(e);
        }

        public LockException(Exception e) {
            super(e);
        }
    }
}
```

Однако есть еще одна проблема с использованием временных узлов zk: поскольку zk полагается на регулярный контрольный сигнал сеанса для поддержания клиента, если клиент входит в длинный GC, это может заставить zk подумать, что клиент не работает, и снять блокировку, позволяя другим клиентам получить блокировку. Однако после восстановления GC клиент будет думать, что он все еще удерживает блокировку, поэтому несколько клиентов могут получить блокировку одновременно. [#209](https://github.com/doocs/advanced-java/issues/209)

В этой ситуации вы можете использовать настройку JVM, чтобы избежать долгосрочных ситуаций со сборкой мусора.

### Сравнение распределенной блокировки redis и распределенной блокировки zk

— перераспределить распределенную блокировку, по сути, вам нужно постоянно пытаться получить блокировку самостоятельно, что съедает производительность.
- zk распределенная блокировка, если вы не можете получить блокировку, просто зарегистрируйте прослушиватель. Нет необходимости постоянно активно пытаться получить блокировку, а издержки производительности невелики.

Другой момент заключается в том, что если клиент, которому Redis получает блокировку, обнаруживает ошибку и зависает, блокировку можно снять только после ожидания периода ожидания; с помощью zk, поскольку создается временный znode, пока клиент зависает, znode исчезнет, ​​и в это время блокировка будет снята автоматически.

Вы не находите распределенную блокировку Redis проблематичной? Блокировка обхода, время расчета и т. д. Семантика распределенной блокировки zk понятна и проста в реализации.

Итак, не анализируя слишком много вещей, я просто расскажу об этих двух моментах. По своей личной практике я считаю, что распределенная блокировка zk более надежна, чем распределенная блокировка Redis, а модель проста и удобна в использовании.
