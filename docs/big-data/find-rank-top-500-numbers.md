# Как найти 500 лучших номеров?

## Постановка задачи

Имеется 20 массивов по 500 элементов каждый, расположенных в отсортированном порядке. Как найти первые 500 номеров среди этих 20\*500 номеров?

## Подход к решению

Для задач TopK наиболее распространенным подходом является использование пирамидальной сортировки. Для этого вопроса, предполагая, что массив расположен в порядке убывания, можно использовать следующий метод:

Сначала создайте большую верхнюю кучу. Размер кучи — это количество массивов, равное 20. Сохраняйте максимальное значение каждого массива в куче.

Затем удалите верхний элемент кучи, сохраните его в другом массиве размером 500, а затем вставьте следующий элемент массива, в котором находится удаленный элемент, в большую верхнюю кучу.

Повторяйте описанные выше действия до тех пор, пока не будет удален 500-й элемент, то есть не будут найдены первые 500 самых больших чисел.

> Чтобы узнать, из какого массива оно было взято после извлечения фрагмента данных из кучи, чтобы можно было извлечь значение из массива, указатель массива может быть сохранен в куче и может быть предоставлен метод сравнения размера указателя.

```java
import lombok.Data;

import java.util.Arrays;
import java.util.PriorityQueue;

/**
 * @author https://github.com/yanglbme
 */
@Data
public class DataWithSource implements Comparable<DataWithSource> {
    /**
     * 数值
     */
    private int value;

    /**
     * 记录数值来源的数组
     */
    private int source;

    /**
     * 记录数值在数组中的索引
     */
    private int index;

    public DataWithSource(int value, int source, int index) {
        this.value = value;
        this.source = source;
        this.index = index;
    }

    /**
     *
     * 由于 PriorityQueue 使用小顶堆来实现，这里通过修改
     * 两个整数的比较逻辑来让 PriorityQueue 变成大顶堆
     */
    @Override
    public int compareTo(DataWithSource o) {
        return Integer.compare(o.getValue(), this.value);
    }
}

class Test {
    public static int[] getTop(int[][] data) {
        int rowSize = data.length;
        int columnSize = data[0].length;

        // 创建一个columnSize大小的数组，存放结果
        int[] result = new int[columnSize];

        PriorityQueue<DataWithSource> maxHeap = new PriorityQueue<>();
        for (int i = 0; i < rowSize; ++i) {
            // 将每个数组的最大一个元素放入堆中
            DataWithSource d = new DataWithSource(data[i][0], i, 0);
            maxHeap.add(d);
        }

        int num = 0;
        while (num < columnSize) {
            // 删除堆顶元素
            DataWithSource d = maxHeap.poll();
            result[num++] = d.getValue();
            if (num >= columnSize) {
                break;
            }

            d.setValue(data[d.getSource()][d.getIndex() + 1]);
            d.setIndex(d.getIndex() + 1);
            maxHeap.add(d);
        }
        return result;

    }

    public static void main(String[] args) {
        int[][] data = {
                {29, 17, 14, 2, 1},
                {19, 17, 16, 15, 6},
                {30, 25, 20, 14, 5},
        };

        int[] top = getTop(data);
        System.out.println(Arrays.toString(top)); // [30, 29, 25, 20, 19]
    }
}
```

## Резюме

Ищете TopK, почему бы не рассмотреть возможность сортировки кучи?
