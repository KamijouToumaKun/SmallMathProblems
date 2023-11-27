## A希望行列式不为0，B希望为0（简单）

### Even:

See Putnam 2008: https://math.hawaii.edu/home/pdf/putnam/Putnam_2008.pdf

Alan and Barbara play a game in which they take turns filling entries of an initially empty 2008 × 2008 array.
Alan plays first. At each turn, a player chooses a real number and places it in a vacant entry. The game ends when all the entries are filled. Alan wins if the determinant of the resulting matrix is nonzero; Barbara wins if it is zero. Which player has a winning strategy?

Barbara wins using one of the following strategies.
First solution: Pair each entry of the first row with the entry directly below it in the second row. If Alan ever writes a number in one of the first two rows, Barbara
writes the same number in the other entry in the pair. If Alan writes a number anywhere other than the first two rows, Barbara does likewise. At the end, the resulting matrix will have two identical rows, so its determinant will be zero.
Second solution: (by Manjul Bhargava) Whenever Alan writes a number x in an entry in some row, Barbara writes −x in some other entry in the same row. At the end, the resulting matrix will have all rows summing to zero, so it cannot have full rank.

n=偶数都是一样的，只需每填一个x就在同一行填一个-x，这样每一行的和都是0，因此不满秩

### Odd: n=3:

See Putnam 2002: https://prase.cz/kalva/putnam/psoln/psol024.html

B wins. The determinant is certainly zero if we have a row or column or zeros or if we have two identical rows. We show that the second player can always achieve one of these outcomes.

The absolute value of a determinant is not affected if the rows or columns are permuted, so there is no loss of generality in assuming that the first player's first move is at the top right. The second player then plays in the middle.

因为可以交换任意两行或者两列，不失一般性，先手的第一个数字总是等价于填在左上角
然后后手填在中间
先手要阻挡后手的三个数字连成一行或者一列（三子棋）
但就算如此，后手能放4个0，且保证它们形成一个2x2的子矩阵，因此将行列式展开还是0

### 其他奇数：不确定

See: https://math.stackexchange.com/questions/216503/alice-and-bob-play-the-determinant-game



## 反过来，A希望行列式为0，B希望不为0

See: https://www.zhihu.com/question/264522511/answer/281895230

### 当n = 1，n = 2，甲可通过填0必胜，因为可以轻易让一行或者一列全为0；

### 当n >= 3且为奇数，甲必胜。
不妨设(y, x)代表矩阵第y行第x列的位置。甲的目标是构造两行/列对应相等的数。
（1）甲先在(1, 1)填任意数。
（2）此后，若乙在(2, x)或(3, x)填任意数a，则甲对应地在(3, x)或(2, x)填a；若乙在第2、3行以外的位置填任意数，则甲也在第2、3行以外的位置填任意数。
（3）由于n是奇数，可知矩阵A除去第2、3行后有n * (n - 2)（奇数）个位置，那么按照上述策略，甲一定会填掉这些位置中最后剩下的一个，且此时第2、3行对应位置的数字都是相等的；此后，乙只能在第2、3行填数（若有空位），而甲必能使得第2、3行的数字全部对应相等。

### 当n为偶数，对角占优矩阵？？？
