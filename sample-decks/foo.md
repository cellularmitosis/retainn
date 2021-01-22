format: md1

# Golang Syntax

Some [flashcards](https://gist.github.com/cellularmitosis/530196ad25801ef5a4607ee480ee7034) about [golang](https://golang.org/) syntax.

---

Declare an empty function which returns nothing.

```
fake1

%

fake2
```

%

```go
func foo() {

}
```

---

Declare a function which returns an `int`.

%

```go
func foo() int {
  return 1
}
```

---

Declare a function which takes a `string` and returns `true`.

%

```go
func foo(name string) bool {
  return true
}
```

---

Declare a function which takes a pointer to a `sync.WaitGroup`.

%

```go
func foo(wg *sync.WaitGroup) {

}
```

---

Write a function with a statement which executes after the function has executed.

%

```go
func foo() int {
  defer bar()
  return 42
}
```
