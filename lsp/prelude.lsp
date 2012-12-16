(defmacro let (pairs exp)
	`((fn ~(slice pairs 0 (len pairs) 2) ~exp)
		~@(slice pairs 1 (len pairs) 2)))

(defmacro defn (name args & body)
	`(def ~name (fn ~args (do ~@body))))

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

(defn rest (coll)
	(slice coll 1 (len coll)))

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

(defn range (start stop & args)
	(let (step (if (empty? args) 1 (first args)))
		((fn gen-list (n)
			(if (< n stop)
				(concat (list n) (gen-list (+ n step)))
				(list)))
			start)))
