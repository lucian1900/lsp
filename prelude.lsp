(defmacro defn (name args body)
  `(def ~name (fn (~@args) ~body)))

(defmacro let (pairs exp)
  `((fn (~@(slice pairs 0 (len pairs) 2)) ~exp)
    ~@(slice pairs 1 (len pairs) 2)))

(defn comp (f g)
  (fn (& xs)
    (f (apply g xs))))

(defn partial (f & args)
  (fn (& xs)
    (apply f (concat args xs))))

(defn inc (x) (+ x 1))

(defn dec (x) (- x 1))

(defn first (coll)
  (coll 0))

(defn second (coll)
  (coll 1))

(defn reduce (fun acc coll)
  (if (empty? coll)
    acc
    (reduce fun (fun acc (first coll)) (rest coll))))

(defn map (fun coll)
  (reduce
    (fn (acc e) (concat acc (list (fun e))))
    '() coll))

(defn filter (pred coll)
  (reduce
    (fn (acc e)
      (if (pred e)
        (concat acc (list e))
        acc))
    '() coll))