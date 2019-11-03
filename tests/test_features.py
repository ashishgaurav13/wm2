from tools.design import Feature, Features

def test_feature_simple():
    f = Feature('x', 1.20)
    assert(f.name == 'x')
    assert(f.value == 1.2)
    assert(str(f) == 'x:1.2')

def test_features_simple():
    f = Features({
        'a': 1.3,
        'b': 1.1,
    })
    assert(f['a'] == 1.3)
    assert(f.o['b'].name == 'b') # o = objects
    f['d'] = 2.20
    assert(f.o['d'] == 'd:2.2')
    assert(round(f['a']-f['b'], 1) == 0.2)