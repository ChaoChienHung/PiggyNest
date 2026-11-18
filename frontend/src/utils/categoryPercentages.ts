export interface CategoryAmount {
    name: string;
    value: number;
}

/** Round shares to tenths using largest remainders, preserving a 100.0% total. */
export const categoryPercentTenths = (data: CategoryAmount[]) => {
    const total = data.reduce((sum, item) => sum + item.value, 0);
    if (total <= 0) return data.map(() => 0);
    const exact = data.map(item => item.value / total * 1000);
    const rounded = exact.map(Math.floor);
    const order = exact.map((value, index) => ({ index, fraction: value - rounded[index] }))
        .sort((a, b) => b.fraction - a.fraction || a.index - b.index);
    let remaining = 1000 - rounded.reduce((sum, value) => sum + value, 0);
    for (const item of order) {
        if (remaining-- <= 0) break;
        rounded[item.index] += 1;
    }
    return rounded;
};
