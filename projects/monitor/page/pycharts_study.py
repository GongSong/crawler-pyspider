from example.commons import Faker
from pyecharts import options as opts
from pyecharts.charts import Line


def line_base() -> Line:
    c = (
        Line()
            .add_xaxis(Faker.choose())
            .add_yaxis("商家A", Faker.values(), is_smooth=True)
            .add_yaxis("商家B", Faker.values(), is_smooth=True)
            .set_global_opts(title_opts=opts.TitleOpts(title="Line-基本示例"))
    )
    return c


a = line_base().render()
