# Как реализовать распределенный сеанс?

## Вопрос на собеседовании

Как реализовать распределенный сеанс во время развертывания кластера?

## Что хочет знать интервьюер

Интервьюер много спрашивал вас о том, как играть в Даббо. Если вы умеете играть в Dubbo, вы можете превратить одну систему в распределенную. После раздачи будет много проблем. Самые большие проблемы — это **распределённая транзакция**, **идемпотентность интерфейса**, **распределённая блокировка** и последняя проблема — **распределённый сеанс**.

Конечно, в распределенных системах есть и больше проблем, чем только эта. Есть много и очень сложных проблем. Вот лишь несколько распространенных вопросов, которые также часто задают на собеседованиях.

## Анализ вопросов на собеседовании

Что такое сессия? В браузере есть cookie. Этот файл cookie существует в течение определенного периода времени, и каждый раз, когда отправляется запрос, он возвращает специальный `jsessionid cookie`. На основании этого на стороне сервера можно поддерживать соответствующее поле Session и размещать в нем некоторые данные.

Вообще говоря, пока вы не закроете браузер и файл cookie все еще существует, соответствующий сеанс будет существовать. Но если файл cookie исчезнет, ​​сеанс также исчезнет. Обычно используется в корзинах покупок и т.п., а также для сохранения статуса входа и т.п.

Об этом особо нечего сказать, это должен знать каждый, кто знает Java.

Можно использовать такой сеанс, когда у вас одноблочная система, но если у вас распределенная система, где сохраняются состояния сеанса с таким количеством сервисов?

На самом деле способов существует множество, но наиболее часто используемые из них следующие:

### Нет необходимости использовать сеанс вообще

Используйте токен JWT для хранения идентификационных данных пользователя, а затем получения другой информации из базы данных или кеша. Таким образом, не имеет значения, какому серверу назначен запрос.

### Томкэт + Redis

На самом деле это довольно удобно: просто используйте код сеанса, как и раньше, он по-прежнему основан на встроенной поддержке сеанса Tomcat, а затем используйте что-то под названием `Tomcat RedisSessionManager`, чтобы все Tomcats, которые мы развертываем, сохраняли данные сеанса в Redis.

Настройте в файле конфигурации Tomcat:

```xml
<Valve className="com.orangefunction.tomcat.redissessions.RedisSessionHandlerValve" />

<Manager className="com.orangefunction.tomcat.redissessions.RedisSessionManager"
         host="{redis.host}"
         port="{redis.port}"
         database="{redis.dbnum}"
         maxInactiveInterval="60"/>
```

Затем укажите хост и порт Redis, и все будет в порядке.

```xml
<Valve className="com.orangefunction.tomcat.redissessions.RedisSessionHandlerValve" />
<Manager className="com.orangefunction.tomcat.redissessions.RedisSessionManager"
	 sentinelMaster="mymaster"
	 sentinels="<sentinel1-ip>:26379,<sentinel2-ip>:26379,<sentinel3-ip>:26379"
	 maxInactiveInterval="60"/>
```

Вы также можете использовать описанный выше метод для сохранения данных сеанса на основе кластера высокой доступности Redis, поддерживаемого Redis Sentinel, и это нормально.

### Весенняя сессия + Redis

Второй метод, упомянутый выше, будет тесно связан с контейнером Tomcat. Если я хочу перенести веб-контейнер в Jetty, нужно ли мне снова перенастраивать Jetty?

Потому что описанный выше метод Tomcat + Redis прост в использовании, но он будет сильно зависеть от веб-контейнера, и его сложно пересадить код в другие веб-контейнеры, особенно если вы измените стек технологий? Например, как насчет перехода на Spring Cloud или Spring Boot?

Поэтому теперь лучше использовать универсальное решение на основе Java — Spring. Spring в основном сжимает большинство фреймворков, которые нам нужно использовать. Spring Cloud предоставляет микросервисы, а Spring Boot — создание шаблонов, поэтому использование Spring Session — хороший выбор.

Настройте в pom.xml:

```xml
<dependency>
  <groupId>org.springframework.session</groupId>
  <artifactId>spring-session-data-redis</artifactId>
  <version>1.2.1.RELEASE</version>
</dependency>
<dependency>
  <groupId>redis.clients</groupId>
  <artifactId>jedis</artifactId>
  <version>2.8.1</version>
</dependency>
```

Настройте в файле конфигурации Spring:

```xml
<bean id="redisHttpSessionConfiguration"
     class="org.springframework.session.data.redis.config.annotation.web.http.RedisHttpSessionConfiguration">
    <property name="maxInactiveIntervalInSeconds" value="600"/>
</bean>

<bean id="jedisPoolConfig" class="redis.clients.jedis.JedisPoolConfig">
    <property name="maxTotal" value="100" />
    <property name="maxIdle" value="10" />
</bean>

<bean id="jedisConnectionFactory"
      class="org.springframework.data.redis.connection.jedis.JedisConnectionFactory" destroy-method="destroy">
    <property name="hostName" value="${redis_hostname}"/>
    <property name="port" value="${redis_port}"/>
    <property name="password" value="${redis_pwd}" />
    <property name="timeout" value="3000"/>
    <property name="usePool" value="true"/>
    <property name="poolConfig" ref="jedisPoolConfig"/>
</bean>
```

Настройте в web.xml:

```xml
<filter>
    <filter-name>springSessionRepositoryFilter</filter-name>
    <filter-class>org.springframework.web.filter.DelegatingFilterProxy</filter-class>
</filter>
<filter-mapping>
    <filter-name>springSessionRepositoryFilter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

Пример кода:

```java
@RestController
@RequestMapping("/test")
public class TestController {

    @RequestMapping("/putIntoSession")
    public String putIntoSession(HttpServletRequest request, String username) {
        request.getSession().setAttribute("name",  "leo");
        return "ok";
    }

    @RequestMapping("/getFromSession")
    public String getFromSession(HttpServletRequest request, Model model){
        String name = request.getSession().getAttribute("name");
        return name;
    }
}
```

Приведенный выше код в порядке. Настройте Spring Session для хранения данных сеанса на основе Redis, а затем настройте фильтр Spring Session. В этом случае операции, связанные с сеансом, будут переданы Spring Session. Затем в коде используйте собственную операцию Session, которая предназначена для получения данных из Redis непосредственно на основе Spring Session.

Существует множество способов реализации распределенных сеансов. Я говорю лишь о некоторых наиболее распространенных способах. Первоначально Tomcat + Redis чаще использовался, но будет повторно связан с Tomcat. В последние годы это было реализовано посредством Spring Session.
